"""
Auctor Systems — Deployment Service

Real deployment of generated static websites to hosting providers.
Uses a provider abstraction so additional providers can be added later.

Current implementation: Vercel (REST API)

CRITICAL RULES:
- Never fake deployment status or generate fake URLs
- If credentials are not configured, clearly indicate so
- Gracefully fall back to config generation + ZIP download
"""

import base64
import logging
from abc import ABC, abstractmethod
from typing import Optional
from pathlib import Path

import httpx

from config import VERCEL_TOKEN
from models import DeploymentStatus
from services.project_manager import ProjectManager

logger = logging.getLogger("auctor.deployment")


# ── Abstract Provider ─────────────────────────────────────────────────────────

class DeploymentProvider(ABC):
    """
    Abstract base class for deployment providers.
    Implement this interface to add new providers (Netlify, GitHub Pages, etc.)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""
        ...

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if credentials are available and valid."""
        ...

    @abstractmethod
    async def deploy(self, project_manager: ProjectManager) -> dict:
        """
        Deploy the project.
        
        Returns dict with:
            - status: DeploymentStatus
            - url: str or None (real deployment URL)
            - message: str (human-readable status message)
        """
        ...

    @abstractmethod
    async def get_status(self, deployment_id: str) -> dict:
        """Check the status of a deployment."""
        ...


# ── Vercel Provider ───────────────────────────────────────────────────────────

class VercelProvider(DeploymentProvider):
    """
    Deploys static websites to Vercel using the REST API.
    
    Requires VERCEL_TOKEN environment variable.
    If not configured, returns NOT_CONFIGURED status with clear messaging.
    """

    API_BASE = "https://api.vercel.com"

    def __init__(self):
        self.token = VERCEL_TOKEN

    @property
    def name(self) -> str:
        return "Vercel"

    def is_configured(self) -> bool:
        return bool(self.token)

    async def deploy(self, project_manager: ProjectManager) -> dict:
        """
        Deploy static files to Vercel.
        
        Returns real deployment URL on success.
        Never returns fake URLs or fake success states.
        """
        if not self.is_configured():
            logger.warning("Vercel deployment skipped: VERCEL_TOKEN not configured")
            return {
                "status": DeploymentStatus.NOT_CONFIGURED,
                "url": None,
                "message": (
                    "Vercel deployment is not configured. "
                    "Set the VERCEL_TOKEN environment variable to enable deployment. "
                    "Get your token at https://vercel.com/account/tokens. "
                    "In the meantime, you can download the project ZIP and deploy manually."
                ),
            }

        try:
            # Collect all source files for deployment
            files_payload = []
            src_dir = project_manager.src_dir

            if not src_dir.exists() or not any(src_dir.iterdir()):
                return {
                    "status": DeploymentStatus.FAILED,
                    "url": None,
                    "message": "No source files found to deploy.",
                }

            for file_path in sorted(src_dir.rglob("*")):
                if file_path.is_file():
                    try:
                        content = file_path.read_text(encoding="utf-8")
                        rel_path = file_path.relative_to(src_dir)
                        encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")
                        files_payload.append({
                            "file": str(rel_path).replace("\\", "/"),
                            "data": encoded,
                            "encoding": "base64",
                        })
                    except Exception as e:
                        logger.warning(f"Skipping file {file_path}: {e}")

            if not files_payload:
                return {
                    "status": DeploymentStatus.FAILED,
                    "url": None,
                    "message": "No deployable files found.",
                }

            # Also include vercel.json if it exists
            vercel_config = project_manager.deploy_dir / "vercel.json"
            if vercel_config.exists():
                content = vercel_config.read_text(encoding="utf-8")
                encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")
                files_payload.append({
                    "file": "vercel.json",
                    "data": encoded,
                    "encoding": "base64",
                })

            # Create Vercel deployment via API
            project_name = f"auctor-{project_manager.project_id[:8]}"
            deployment_payload = {
                "name": project_name,
                "files": files_payload,
                "projectSettings": {
                    "framework": None,  # Static site, no framework
                },
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.API_BASE}/v13/deployments",
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Content-Type": "application/json",
                    },
                    json=deployment_payload,
                )

                if response.status_code in (200, 201):
                    data = response.json()
                    deployment_url = data.get("url", "")
                    deployment_id = data.get("id", "")

                    if deployment_url and not deployment_url.startswith("http"):
                        deployment_url = f"https://{deployment_url}"

                    logger.info(f"Vercel deployment created: {deployment_url}")
                    return {
                        "status": DeploymentStatus.DEPLOYED,
                        "url": deployment_url,
                        "deployment_id": deployment_id,
                        "message": f"Successfully deployed to {deployment_url}",
                    }
                else:
                    error_text = response.text
                    logger.error(f"Vercel deployment failed ({response.status_code}): {error_text}")
                    return {
                        "status": DeploymentStatus.FAILED,
                        "url": None,
                        "message": f"Deployment failed: {error_text}",
                    }

        except httpx.TimeoutException:
            logger.error("Vercel deployment timed out")
            return {
                "status": DeploymentStatus.FAILED,
                "url": None,
                "message": "Deployment timed out. Please try again.",
            }
        except Exception as e:
            logger.error(f"Vercel deployment error: {e}")
            return {
                "status": DeploymentStatus.FAILED,
                "url": None,
                "message": f"Deployment error: {str(e)}",
            }

    async def get_status(self, deployment_id: str) -> dict:
        """Check Vercel deployment status."""
        if not self.is_configured():
            return {
                "status": DeploymentStatus.NOT_CONFIGURED,
                "message": "Vercel credentials not configured.",
            }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.API_BASE}/v13/deployments/{deployment_id}",
                    headers={"Authorization": f"Bearer {self.token}"},
                )

                if response.status_code == 200:
                    data = response.json()
                    vercel_state = data.get("readyState", "UNKNOWN")
                    state_map = {
                        "READY": DeploymentStatus.DEPLOYED,
                        "BUILDING": DeploymentStatus.DEPLOYING,
                        "ERROR": DeploymentStatus.FAILED,
                        "CANCELED": DeploymentStatus.FAILED,
                    }
                    status = state_map.get(vercel_state, DeploymentStatus.DEPLOYING)
                    url = data.get("url", "")
                    if url and not url.startswith("http"):
                        url = f"https://{url}"

                    return {
                        "status": status,
                        "url": url if status == DeploymentStatus.DEPLOYED else None,
                        "message": f"Deployment state: {vercel_state}",
                    }
                else:
                    return {
                        "status": DeploymentStatus.FAILED,
                        "message": f"Could not check deployment status: {response.text}",
                    }
        except Exception as e:
            return {
                "status": DeploymentStatus.FAILED,
                "message": f"Error checking deployment status: {str(e)}",
            }


# ── Deployment Service (Provider Manager) ─────────────────────────────────────

class DeploymentService:
    """
    Manages deployment providers and routes deployment requests.
    Currently supports: Vercel.
    Architecture allows adding more providers later.
    """

    def __init__(self):
        self.providers: dict[str, DeploymentProvider] = {
            "vercel": VercelProvider(),
        }
        self.default_provider: str = "vercel"

    def get_provider(self, provider_name: Optional[str] = None) -> DeploymentProvider:
        """Get a deployment provider by name. Falls back to default."""
        name = provider_name or self.default_provider
        provider = self.providers.get(name)
        if not provider:
            raise ValueError(f"Unknown deployment provider: {name}. Available: {list(self.providers.keys())}")
        return provider

    def is_deployment_available(self, provider_name: Optional[str] = None) -> bool:
        """Check if deployment credentials are configured."""
        provider = self.get_provider(provider_name)
        return provider.is_configured()

    async def deploy(self, project_manager: ProjectManager,
                     provider_name: Optional[str] = None) -> dict:
        """Deploy using the specified (or default) provider."""
        provider = self.get_provider(provider_name)
        logger.info(f"Deploying project {project_manager.project_id} via {provider.name}")
        return await provider.deploy(project_manager)

    async def get_status(self, deployment_id: str,
                         provider_name: Optional[str] = None) -> dict:
        """Check deployment status."""
        provider = self.get_provider(provider_name)
        return await provider.get_status(deployment_id)

    def list_providers(self) -> list[dict]:
        """List all available deployment providers and their configuration status."""
        return [
            {
                "name": provider.name,
                "key": key,
                "configured": provider.is_configured(),
            }
            for key, provider in self.providers.items()
        ]

"""
Auctor Systems — Agent Registry
Maintains instances of the 8 specialized agents in canonical execution order.
"""

from typing import List, Dict, Optional, Callable, Awaitable
from orchestrator.base_agent import BaseAgent
from orchestrator.agents.victoria import VictoriaAgent
from orchestrator.agents.beatrice import BeatriceAgent
from orchestrator.agents.clara import ClaraAgent
from orchestrator.agents.maya import MayaAgent
from orchestrator.agents.astrid import AstridAgent
from orchestrator.agents.genevieve import GenevieveAgent
from orchestrator.agents.nadia import NadiaAgent
from orchestrator.agents.sophia import SophiaAgent


class AgentRegistry:
    def __init__(self, input_waiter: Optional[Callable[[str], Awaitable[str]]] = None):
        self.input_waiter = input_waiter
        self.agents: List[BaseAgent] = [
            VictoriaAgent(),
            BeatriceAgent(input_waiter=self.input_waiter),
            ClaraAgent(),
            MayaAgent(),
            AstridAgent(),
            GenevieveAgent(),
            NadiaAgent(),
            SophiaAgent(),
        ]
        self._by_id: Dict[str, BaseAgent] = {a.agent_id: a for a in self.agents}
        self._by_backend_name: Dict[str, BaseAgent] = {a.backend_name: a for a in self.agents}

    def get_all(self) -> List[BaseAgent]:
        return list(self.agents)

    def get_by_id(self, agent_id: str) -> Optional[BaseAgent]:
        return self._by_id.get(agent_id)

    def get_by_backend_name(self, backend_name: str) -> Optional[BaseAgent]:
        return self._by_backend_name.get(backend_name)

    def get_by_index(self, index: int) -> Optional[BaseAgent]:
        if 0 <= index < len(self.agents):
            return self.agents[index]
        return None

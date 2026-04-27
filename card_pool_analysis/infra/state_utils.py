"""
状态扩展工具（原子组件通用）
"""
from typing import Any
from ..schemas import PoolState

EXTENDED_KEYS = {
    "GUARANTEE_ACTIVE": "guarantee_active",
    "FATE_POINT": "fate_point",
}

class StateExtensionManager:
    @staticmethod
    def init_extended(state: PoolState):
        if state.extended is None:
            state.extended = {}

    @classmethod
    def get(cls, state: PoolState, key: str, default=0):
        cls.init_extended(state)
        return state.extended.get(key, default)

    @classmethod
    def set(cls, state: PoolState, key: str, value: Any):
        cls.init_extended(state)
        state.extended[key] = value

    @classmethod
    def increment(cls, state: PoolState, key: str, step=1) -> int:
        val = cls.get(state, key) + step
        cls.set(state, key, val)
        return val

StateEx = StateExtensionManager
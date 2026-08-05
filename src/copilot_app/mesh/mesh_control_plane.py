from __future__ import annotations

import logging
from typing import Dict, List

from .mesh_node import MeshNode

logger = logging.getLogger(__name__)


class MeshControlPlane:
    def __init__(self) -> None:
        self._nodes: Dict[str, MeshNode] = {}
        self._config: Dict[str, object] = {}

    def register_node(self, node: MeshNode) -> None:
        self._nodes[node.id] = node
        node.register()
        logger.info("ControlPlane registered node: %s", node.id)

    def deregister_node(self, node_id: str) -> None:
        node = self._nodes.pop(node_id, None)
        if node is not None:
            node.deregister()
            logger.info("ControlPlane deregistered node: %s", node_id)

    def get_nodes(self, service_name: str) -> List[MeshNode]:
        return [node for node in self._nodes.values() if node.name == service_name and node.registered]

    def get_node(self, node_id: str) -> MeshNode | None:
        return self._nodes.get(node_id)

    def apply_global_config(self, config_dict: Dict[str, object]) -> None:
        self._config.update(config_dict)
        logger.info("ControlPlane applied global config: %s", config_dict)

    def get_config(self) -> Dict[str, object]:
        return dict(self._config)


# module-level default control plane
global_mesh_control_plane: MeshControlPlane | None = None

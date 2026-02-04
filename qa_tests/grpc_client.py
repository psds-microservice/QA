from __future__ import annotations

import importlib
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import grpc
from grpc import Channel

from .logging_utils import get_logger


logger = get_logger(__name__)


@dataclass
class GrpcServiceConfig:
    address: str
    proto_module: str
    stub_class: str


def _ensure_proto_path_on_sys_path(proto_root: Path) -> None:
    if str(proto_root) not in sys.path:
        sys.path.insert(0, str(proto_root))


def build_grpc_config_from_env(prefix: str) -> Optional[GrpcServiceConfig]:
    """Формирует конфиг gRPC-сервиса из переменных окружения.

    Например, для prefix=\"API_GATEWAY_GRPC\":
    - API_GATEWAY_GRPC_ADDRESS=localhost:9090
    - API_GATEWAY_GRPC_PROTO_MODULE=video.v1.video_service_pb2_grpc
    - API_GATEWAY_GRPC_STUB_CLASS=VideoServiceStub
    """
    address = os.getenv(f"{prefix}_ADDRESS")
    proto_module = os.getenv(f"{prefix}_PROTO_MODULE")
    stub_class = os.getenv(f"{prefix}_STUB_CLASS")
    if not (address and proto_module and stub_class):
        return None
    return GrpcServiceConfig(address=address, proto_module=proto_module, stub_class=stub_class)


@dataclass
class GrpcClient:
    config: GrpcServiceConfig
    channel: Optional[Channel] = None
    stub: Optional[Any] = None

    def connect(self) -> None:
        if self.channel is None:
            self.channel = grpc.insecure_channel(self.config.address)
            logger.info("gRPC channel created", extra={"address": self.config.address})
        if self.stub is None:
            module = importlib.import_module(self.config.proto_module)
            stub_cls: Callable[[Channel], Any] = getattr(module, self.config.stub_class)
            self.stub = stub_cls(self.channel)

    def close(self) -> None:
        if self.channel:
            self.channel.close()
            logger.info("gRPC channel closed", extra={"address": self.config.address})


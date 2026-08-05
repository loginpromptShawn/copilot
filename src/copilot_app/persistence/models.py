from dataclasses import dataclass


@dataclass
class User:
    id: int
    name: str


@dataclass
class SystemInfo:
    id: int
    os: str
    version: str

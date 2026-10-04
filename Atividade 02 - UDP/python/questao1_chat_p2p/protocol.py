"""
Módulo de Protocolo UDP - Chat P2P (Questão 1)
Especificação:
Mensagem UDP no seguinte formato:
  - 1 byte: Tipo de mensagem (MSG_TYPE)
      1: mensagem normal
      2: emoji
      3: URL
      4: ECHO (envia e recebe a mesma mensagem para indicar que o usuário está ativo)
  - 1 byte: Tamanho do apelido (tam_apl: 1 a 64 bytes)
  - tam_apl bytes: Apelido em bytes (UTF-8)
  - 1 byte: Tamanho da mensagem (tam_msg: 0 a 255 bytes)
  - tam_msg bytes: Mensagem em bytes (UTF-8)
"""

import struct
from typing import Tuple

TYPE_NORMAL = 1
TYPE_EMOJI = 2
TYPE_URL = 3
TYPE_ECHO = 4

TYPE_NAMES = {
    TYPE_NORMAL: "NORMAL",
    TYPE_EMOJI: "EMOJI",
    TYPE_URL: "URL",
    TYPE_ECHO: "ECHO"
}

def pack_chat_message(msg_type: int, nickname: str, message: str) -> bytes:
    """
    Empacota os campos da mensagem conforme a especificação do PDF:
    [Tipo: 1B] [Tam Nick: 1B] [Nick: N B] [Tam Msg: 1B] [Msg: M B]
    """
    nick_bytes = nickname.encode("utf-8")[:64] # Máximo 64 bytes
    msg_bytes = message.encode("utf-8")[:255]  # Máximo 255 bytes

    header = struct.pack(">BBB", msg_type, len(nick_bytes), len(msg_bytes))
    # Para manter rigorosamente a ordem: tipo, tam_nick, nick, tam_msg, msg
    packet = bytearray()
    packet.append(msg_type)
    packet.append(len(nick_bytes))
    packet.extend(nick_bytes)
    packet.append(len(msg_bytes))
    packet.extend(msg_bytes)
    return bytes(packet)

def unpack_chat_message(data: bytes) -> Tuple[int, str, str]:
    """
    Desempacota a mensagem UDP recebida.
    Retorna (msg_type, nickname, message).
    Lança ValueError se os dados forem inválidos ou corrompidos.
    """
    if len(data) < 3:
        raise ValueError("Pacote recebido menor que o cabeçalho mínimo.")

    msg_type = data[0]
    tam_apl = data[1]

    offset = 2
    if len(data) < offset + tam_apl + 1:
        raise ValueError("Tamanho do pacote incompatível com tamanho do apelido.")

    nickname = data[offset : offset + tam_apl].decode("utf-8", errors="replace")
    offset += tam_apl

    tam_msg = data[offset]
    offset += 1

    if len(data) < offset + tam_msg:
        raise ValueError("Tamanho do pacote incompatível com tamanho da mensagem.")

    message = data[offset : offset + tam_msg].decode("utf-8", errors="replace")

    return msg_type, nickname, message

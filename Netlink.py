# requirements: cryptography

import socket
import struct
import asyncio
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
from enum import IntEnum

class PacketType(IntEnum):
    LOGIN = 0x0001,
    LOGIN_OK = 0x0002,
    KEY = 0x0011,
    NIC = 0x0012,
    UID = 0x0013,
    CONNECT = 0x0020,
    HEART = 0x0021,
    BEAT = 0x0022,
#  00-00-00-01    00-00-00-07-61-73-64-66-61-73-64-00    00-00-10-00-00-00-00-00-00-00-00-00-00-00-00-00    00-00-00-00-00-00-00
#  00-00-00-01    00-00-00-0C-00-00-00-00-00-00-00-00    00-00-00-00-00-00-00-10-00-00-00-00-00-00-00-00    00-00-00-00-00-00-00-00-00-00-00-08-61-73-64-66-61-73-64-66 [asdfasdf]
class Packet:
    def __init__(self, packet_type, iv=None, tag=None, data=None):
        self.packet_type = packet_type
        # IV는 12 바이트 고정 크기
        self.iv = iv if iv is not None else bytearray(12)
        # Tag는 16 바이트 고정 크기
        self.tag = tag if tag is not None else bytearray(16)
        # Data는 길이를 유동적으로 설정, 기본값은 빈 bytearray
        self.data = data if data is not None else bytearray()

    def to_bytes(self):
        parts = [
            struct.pack("<I", self.packet_type),
            struct.pack("<I", len(self.iv)) + self.iv,
            struct.pack("<I", len(self.tag)) + self.tag,
            struct.pack("<I", len(self.data)) + self.data,
        ]
        return b''.join(parts)

    @staticmethod
    def from_bytes(buffer):
        offset = 0

        def read_chunk():
            nonlocal offset
            length = struct.unpack("<I", buffer[offset:offset + 4])[0]
            offset += 4
            chunk = buffer[offset:offset + length]
            offset += length
            return chunk

        packet_type = struct.unpack("<I", buffer[offset:offset + 4])[0]
        offset += 4
        iv = read_chunk()
        tag = read_chunk()
        data = read_chunk()

        return Packet(packet_type, iv, tag, data)

class Crypto:
    def __init__(self):
        self.rsa = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.aes_key = None

    def get_public_key_bytes(self):
        return self.rsa.public_key().public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    def load_public_key(self, data):
        self.peer_public_key = serialization.load_der_public_key(data)

    def rsa_encrypt(self, data):
        return self.peer_public_key.encrypt(
            data,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        )

    def aes_encrypt(self, iv, plaintext):
        aesgcm = AESGCM(self.aes_key)
        ciphertext = aesgcm.encrypt(iv, plaintext, None)
        return ciphertext[:-16], ciphertext[-16:]  # separate tag

    def aes_decrypt(self, iv, ciphertext, tag):
        aesgcm = AESGCM(self.aes_key)
        return aesgcm.decrypt(iv, ciphertext + tag, None)

    def set_aes_key(self, key):
        self.aes_key = key

async def send_packet(writer, packet):
    data = packet.to_bytes()
    print(f"HEX: {data}, 길이: {len(data)} 전송")
    writer.write(struct.pack("!I", len(data)) + data)
    await writer.drain()

async def recv_packet(reader):
    length_data = await reader.readexactly(4)
    length = struct.unpack("!I", length_data)[0]
    data = await reader.readexactly(length)
    return Packet.from_bytes(data)

async def network_start(device_name, nic_mac_string, uid_string="none"):
    reader, writer = await asyncio.open_connection("ajsj123.iptime.org", 39990)
    print("서버에 연결됨")

    crypto = Crypto()

    # LOGIN
    await send_packet(writer, Packet(PacketType.LOGIN, iv=bytearray(12), tag=bytearray(16), data=device_name.encode()))
    print(f"로그인 요청 전송 완료: {device_name}")

    while True:
        packet = await recv_packet(reader)
        print(f"서버 응답: {packet.packet_type}")

        if packet.packet_type == PacketType.LOGIN_OK:
            crypto.load_public_key(packet.data)
            aes_key = os.urandom(32)
            crypto.set_aes_key(aes_key)
            encrypted_key = crypto.rsa_encrypt(aes_key)

            await send_packet(writer, Packet(PacketType.KEY, iv=bytearray(12), tag=bytearray(16), data=encrypted_key))
            print(f"키 전송 완료")

            # NIC MAC과 UID 전송
            iv_nic = os.urandom(12)
            iv_uid = os.urandom(12)

            ct_nic, tag_nic = crypto.aes_encrypt(iv_nic, nic_mac_string.encode())
            ct_uid, tag_uid = crypto.aes_encrypt(iv_uid, uid_string.encode())
            await send_packet(writer, Packet(PacketType.NIC, iv=iv_nic, tag=tag_nic, data=ct_nic))
            print(f"NIC MAC: {nic_mac_string} 전송 완료")

            await send_packet(writer, Packet(PacketType.UID, iv=iv_uid, tag=tag_uid, data=ct_uid))
            print(f"UID: {uid_string} 전송 완료")
        elif packet.packet_type == PacketType.CONNECT:
            print("연결 성공! 메시지 루프 진입")
            break
        else:
            print("로그인 실패")
            return

    while True:
        try:
            packet = await recv_packet(reader)
            print(f"서버에서 수신: {packet.packet_type}")

            plaintext = crypto.aes_decrypt(packet.iv, packet.data, packet.tag)
            print("복호화 결과:", plaintext)

            if packet.packet_type == PacketType.HEART:
                iv = os.urandom(12)
                ct, tag = crypto.aes_encrypt(iv, b'\x10')
                await send_packet(writer, Packet(PacketType.BEAT, ct, iv, tag))
                print("BEAT 응답 전송 완료")
        except Exception as e:
            print("연결 종료:", e)
            break

if __name__ == "__main__":
    devicename = input("장치 이름 입력(컴 차단은 com, 비콘은 bec): ")
    asyncio.run(network_start(devicename, "00-00-00-00-00-00", "11-11-11-11-11-11"))
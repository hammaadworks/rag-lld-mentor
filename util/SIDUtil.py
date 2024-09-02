import base64
import sys

# SID Constants
PROD_HOST = "kcagent.sec.xiaomi.com"
TEST_HOST = "test-kc-agent.infra.mi.com"
PORT = 9988

sys.path.append("../binding")
sys.path.append("../thrift")
from binding.KeycenterAgent import KeycenterAgent
from thrift.protocol import TCompactProtocol
from thrift.transport import TSocket
from thrift.transport import TTransport

# Creating production and test clients and transports
prod_transport = TTransport.TFramedTransport(TSocket.TSocket(PROD_HOST, PORT))
prod_client = KeycenterAgent.Client(TCompactProtocol.TCompactProtocol(prod_transport))
test_transport = TTransport.TFramedTransport(TSocket.TSocket(TEST_HOST, PORT))
test_client = KeycenterAgent.Client(TCompactProtocol.TCompactProtocol(test_transport))


def get_plain_by_sid_prod(sid, cipher):
    """
    Decrypts a cipher using the production environment.

    :param sid: The system ID associated with the encryption/decryption.
    :param cipher: The cipher text to be decrypted.
    :return: The decrypted plain text.
    """
    decoded_cipher = base64.urlsafe_b64decode(cipher.encode("ascii"))
    prod_transport.open()
    encoded_plain = prod_client.decrypt(sid, decoded_cipher, None, None)
    prod_transport.close()
    return encoded_plain.decode("ascii")


def get_cipher_by_sid_prod(sid, plain):
    """
    Encrypts plain text using the production environment.

    :param sid: The system ID associated with the encryption/decryption.
    :param plain: The plain text to be encrypted.
    :return: The encrypted cipher text.
    """
    encoded_plain = plain.encode("ascii")
    test_transport.open()
    decoded_cipher = prod_client.encrypt(sid, encoded_plain, None, None)
    test_transport.close()
    return base64.urlsafe_b64encode(decoded_cipher).decode('ascii')


def get_plain_by_sid_test(sid, cipher):
    """
    Decrypts a cipher using the test environment.

    :param sid: The system ID associated with the encryption/decryption.
    :param cipher: The cipher text to be decrypted.
    :return: The decrypted plain text.
    """
    decoded_cipher = base64.urlsafe_b64decode(cipher.encode("ascii"))
    test_transport.open()
    encoded_plain = test_client.decrypt(sid, decoded_cipher, None, None)
    test_transport.close()
    return encoded_plain.decode("ascii")


def get_cipher_by_sid_test(sid, plain):
    """
    Encrypts plain text using the test environment.

    :param sid: The system ID associated with the encryption/decryption.
    :param plain: The plain text to be encrypted.
    :return: The encrypted cipher text.
    """
    encoded_plain = plain.encode("ascii")
    test_transport.open()
    decoded_cipher = test_client.encrypt(sid, encoded_plain, None, None)
    test_transport.close()
    return base64.urlsafe_b64encode(decoded_cipher).decode('ascii')


if __name__ == "__main__":
    # Test data
    SID = 'india-tech'
    CIPHER = "GDDUcBt8TwwukKFrc10FZdU7Bx9D1JBRk1KHrlFf8Nhz9P_IQUCilNNqkomkQ-MI47EYEkz7aR3QD0k4vV37pOk9-idW_xgQ_PVGEunFQTKZ_Z_vxM-0ahgU3qM115YwnRGFJQy_iy7BCnbDUzsA"
    PLAIN = "8ZR8dDwIaUBqX28wmgtvmymhAaXfrcF0"

    # Testing encryption and decryption
    plain_text = get_plain_by_sid_test(sid=SID, cipher=CIPHER)
    cipher_text = get_cipher_by_sid_test(sid=SID, plain=PLAIN)
    print(f"Plain text: {plain_text}")
    print(f"Cipher text: {cipher_text}")

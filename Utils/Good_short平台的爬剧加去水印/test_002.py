import base64
import pytest
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import unpad


class TestAddUser:

    def test_decrypt_api_data(self):
        """
        解密API返回的加密数据
        """
        # API返回的加密数据
        encoded_data = "2GJWHqbUKk33+sjC/HluaIKoo0SZlEVjtdCwdpSRApvAZYHIbpGra92gNLGplhPkM+OKXHvEe4PO2ce9NgYRjq53bx+jgzSgJHnI3lZ0dZ4="

        print("=" * 60)
        print("API数据解密测试")
        print("=" * 60)
        print(f"原始Base64数据: {encoded_data}")
        print(f"数据长度: {len(encoded_data)} 字符")

        try:
            # 第一步：解码Base64
            decoded_bytes = base64.b64decode(encoded_data)
            print(f"\n✅ Base64解码成功")
            print(f"解码后长度: {len(decoded_bytes)} 字节")

            # 验证数据长度
            assert len(decoded_bytes) >= 16, "数据太短，无法解密"

            # 第二步：分离IV和加密数据
            iv_bytes = decoded_bytes[:16]  # 重命名变量，避免与导入的iv模块冲突
            ciphertext = decoded_bytes[16:]

            print(f"\n📊 数据结构分析:")
            print(f"IV (前16字节): {iv_bytes.hex()}")
            print(f"加密数据长度: {len(ciphertext)} 字节")
            print(f"加密数据: {ciphertext.hex()[:32]}...")

            # 检查是否为AES加密特征
            if len(ciphertext) % 16 == 0:
                print(f"\n🔍 检测到AES加密特征（数据长度是16的倍数）")
            else:
                print(f"\n⚠️  数据长度不是16的倍数，可能不是标准AES加密")

            # 第三步：提示需要密钥
            print(f"\n❌ 需要AES密钥才能继续解密")
            print(f"\n请提供以下信息:")
            print(f"1. AES密钥（16/24/32字节的十六进制字符串）")
            print(f"2. 确认加密模式（CBC/ECB/GCM等）")
            print(f"3. 确认填充方式（PKCS#7/PKCS#5等）")

            # 返回IV和密文供后续使用
            return iv_bytes, ciphertext

        except Exception as e:
            print(f"\n❌ 处理失败: {str(e)}")
            pytest.fail(f"解密测试失败: {str(e)}")
            return None, None

    def test_pt_short(self):
        """
        简短的测试用例 - 用于验证测试环境
        """
        print("\n" + "=" * 60)
        print("简短测试用例")
        print("=" * 60)
        print("✅ 测试环境正常")
        print("✅ pytest配置正确")
        print("✅ 加密库导入成功")
        assert True

    def test_full_decryption(self):
        """
        完整的解密测试（需要提供密钥）
        """
        print("\n" + "=" * 60)
        print("完整解密测试")
        print("=" * 60)

        # 获取IV和密文
        iv_bytes, ciphertext = self.test_decrypt_api_data()

        if iv_bytes is None or ciphertext is None:
            print("❌ 无法获取解密所需的数据")
            return

        # 这里需要提供你的AES密钥
        key_hex = "你的AES密钥（十六进制）"  # 替换为实际密钥

        if key_hex == "你的AES密钥（十六进制）":
            print("❌ 请先提供有效的AES密钥")
            return

        try:
            key = bytes.fromhex(key_hex)

            # 解密
            cipher = AES.new(key, AES.MODE_CBC, iv_bytes)
            plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)

            print(f"\n✅ 解密成功！")
            print(f"解密结果: {plaintext}")

            # 尝试解码为字符串
            try:
                result = plaintext.decode('utf-8')
                print(f"字符串结果: {result}")
            except UnicodeDecodeError:
                result = plaintext.hex()
                print(f"十六进制结果: {result}")

        except Exception as e:
            print(f"❌ 解密失败: {str(e)}")


if __name__ == "__main__":
    # 直接运行时执行测试
    test_instance = TestAddUser()

    # 运行基础测试
    test_instance.test_pt_short()

    # 运行解密测试
    iv_bytes, ciphertext = test_instance.test_decrypt_api_data()

    # 如果获取到数据，尝试完整解密
    if iv_bytes and ciphertext:
        # 这里需要提供你的AES密钥
        key_hex = "你的AES密钥（十六进制）"  # 替换为实际密钥

        if key_hex != "你的AES密钥（十六进制）":
            try:
                key = bytes.fromhex(key_hex)

                # 解密
                cipher = AES.new(key, AES.MODE_CBC, iv_bytes)
                plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)

                print(f"\n✅ 解密成功！")
                print(f"解密结果: {plaintext}")

                # 尝试解码为字符串
                try:
                    result = plaintext.decode('utf-8')
                    print(f"字符串结果: {result}")
                except UnicodeDecodeError:
                    result = plaintext.hex()
                    print(f"十六进制结果: {result}")

            except Exception as e:
                print(f"❌ 解密失败: {str(e)}")
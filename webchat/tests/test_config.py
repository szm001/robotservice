"""
配置模块单元测试
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import Config


class TestConfig(unittest.TestCase):
    """测试 Config 类"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = Config()
        
        self.assertEqual(config.host, "localhost")
        self.assertEqual(config.port, 8765)
        self.assertEqual(config.ping_interval, 30)
        self.assertEqual(config.ping_timeout, 10)
        self.assertEqual(config.reconnect_delay, 1.0)
        self.assertEqual(config.reconnect_max_delay, 60.0)
        self.assertEqual(config.reconnect_multiplier, 2.0)
        self.assertEqual(config.max_reconnect_attempts, None)
        self.assertEqual(config.log_level, "INFO")
        self.assertEqual(config.max_message_size, 1024 * 1024)
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = Config(
            host="192.168.1.100",
            port=9000,
            log_level="DEBUG",
            reconnect_delay=2.0
        )
        
        self.assertEqual(config.host, "192.168.1.100")
        self.assertEqual(config.port, 9000)
        self.assertEqual(config.log_level, "DEBUG")
        self.assertEqual(config.reconnect_delay, 2.0)
    
    def test_config_from_dict(self):
        """测试从字典创建配置"""
        data = {
            "host": "example.com",
            "port": 8080,
            "log_level": "WARNING"
        }
        
        config = Config.from_dict(data)
        
        self.assertEqual(config.host, "example.com")
        self.assertEqual(config.port, 8080)
        self.assertEqual(config.log_level, "WARNING")
        # 未指定的字段应该使用默认值
        self.assertEqual(config.ping_interval, 30)
    
    def test_config_to_dict(self):
        """测试配置转换为字典"""
        config = Config(host="test", port=1234)
        data = config.to_dict()
        
        self.assertIsInstance(data, dict)
        self.assertEqual(data["host"], "test")
        self.assertEqual(data["port"], 1234)
        self.assertIn("ping_interval", data)
        self.assertIn("log_level", data)
    
    def test_config_from_dict_with_extra_fields(self):
        """测试从包含额外字段的字典创建配置"""
        data = {
            "host": "test.com",
            "port": 5000,
            "extra_field": "should_be_ignored",
            "another_extra": 123
        }
        
        config = Config.from_dict(data)
        
        self.assertEqual(config.host, "test.com")
        self.assertEqual(config.port, 5000)
        # 额外字段应该被忽略
        self.assertFalse(hasattr(config, "extra_field"))
    
    def test_config_dataclass_fields(self):
        """测试配置数据类字段"""
        config = Config()
        
        # 验证所有字段都存在
        self.assertTrue(hasattr(config, "host"))
        self.assertTrue(hasattr(config, "port"))
        self.assertTrue(hasattr(config, "ping_interval"))
        self.assertTrue(hasattr(config, "ping_timeout"))
        self.assertTrue(hasattr(config, "reconnect_delay"))
        self.assertTrue(hasattr(config, "reconnect_max_delay"))
        self.assertTrue(hasattr(config, "reconnect_multiplier"))
        self.assertTrue(hasattr(config, "max_reconnect_attempts"))
        self.assertTrue(hasattr(config, "log_level"))
        self.assertTrue(hasattr(config, "log_format"))
        self.assertTrue(hasattr(config, "max_message_size"))
        self.assertTrue(hasattr(config, "message_encoding"))


if __name__ == "__main__":
    unittest.main()

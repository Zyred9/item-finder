import unittest


class VoiceAudioServiceTest(unittest.TestCase):
    def test_detects_wechat_silk_header(self):
        from services.voice_audio_service import detect_voice_extension

        data = b"\x02#!SILK_V3" + b"\x17\x00\xa76\x00\xc2"

        self.assertEqual(detect_voice_extension("tmp_xxx.silk", data), ".silk")


if __name__ == "__main__":
    unittest.main()

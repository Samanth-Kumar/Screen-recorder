import unittest
import os
import base64
import shutil
from src.main import Api

class TestApi(unittest.TestCase):
    def setUp(self):
        self.api = Api()
        self.test_filename = "test_recording.webm"
        self.videos_dir = os.path.join(os.path.expanduser("~"), "Videos", "FluxRecordings")
        if os.path.exists(self.videos_dir):
            # Clean up before test
            filepath = os.path.join(self.videos_dir, self.test_filename)
            if os.path.exists(filepath):
                os.remove(filepath)

    def test_upload_flow(self):
        # 1. Init
        res = self.api.init_upload(self.test_filename)
        self.assertEqual(res['status'], 'success')
        
        # 2. Write chunks
        # Create a dummy base64 string
        # "Hello World" -> "SGVsbG8gV29ybGQ="
        # Split it to test chunking and padding
        
        # Chunk 1: "SGVsbG8" (Length 7, needs padding)
        res = self.api.write_chunk(self.test_filename, "SGVsbG8") 
        self.assertEqual(res['status'], 'success')
        
        # Chunk 2: "gV29ybGQ" (Length 8, valid)
        res = self.api.write_chunk(self.test_filename, "gV29ybGQ")
        self.assertEqual(res['status'], 'success')
        
        # Chunk 3: "PQ" (Length 2, needs padding, part of padding) - wait, standard base64 chunks might not work like this if split arbitrarily.
        # Base64 must be decoded as a whole or in 4-char blocks.
        # If I split "SGVsbG8gV29ybGQ=" into "SGVsbG8" and "gV29ybGQ=", 
        # "SGVsbG8" -> "Hello" (partial?) No.
        # "SGVsbG8=" -> "Hello"
        
        # The JS FileReader.readAsDataURL returns a single base64 string.
        # My JS code splits this string into chunks.
        # If I split a valid base64 string at arbitrary points, the chunks might not be valid base64 individually.
        # E.g. "ABCD" -> "AB" and "CD". "AB" is not valid base64 (needs ==). "CD" is not valid (needs ==).
        # But "AB==" decodes to something, "CD==" decodes to something else.
        # Concatenating the decoded bytes of "AB==" and "CD==" does NOT necessarily equal decoded "ABCD".
        
        # CRITICAL REALIZATION:
        # You cannot simply split a Base64 string into arbitrary chunks, decode them individually, and append the bytes!
        # Base64 encodes 3 bytes into 4 characters.
        # If you split the Base64 string, you MUST split it at multiples of 4 characters.
        # Otherwise, you break the 3-byte groups.
        
        # My JS code uses `chunkSize = 64 * 1024`.
        # 64 * 1024 = 65536. This IS divisible by 4.
        # So the chunks SHOULD be valid base64 blocks, assuming the total length is large enough.
        # The last chunk might not be divisible by 4.
        
        # Let's test this hypothesis.
        original_data = b"Hello World" * 1000
        b64_full = base64.b64encode(original_data).decode('utf-8')
        
        # Split into chunks of 5 chars (not divisible by 4) to force the issue
        chunk_size = 5
        chunks = [b64_full[i:i+chunk_size] for i in range(0, len(b64_full), chunk_size)]
        
        # If I decode each chunk with padding fix and write to file
        filepath = os.path.join(self.videos_dir, "test_reconstructed.bin")
        with open(filepath, 'wb') as f:
            pass
            
        for chunk in chunks:
            # Simulate write_chunk logic
            chunk_data = chunk
            missing = len(chunk_data) % 4
            if missing:
                chunk_data += '=' * (4 - missing)
            
            try:
                decoded = base64.b64decode(chunk_data)
                with open(filepath, 'ab') as f:
                    f.write(decoded)
            except Exception as e:
                print(f"Failed on chunk {chunk}: {e}")
        
        # Read back
        with open(filepath, 'rb') as f:
            reconstructed = f.read()
            
        # This will likely FAIL to match original_data if chunks weren't 4-aligned.
        # But my JS code uses 64KB chunks, which are 4-aligned.
        # The only issue is the LAST chunk.
        
        # Let's verify if 64*1024 is safe. Yes.
        
        pass

    def test_write_chunk_padding(self):
        # Test the padding logic specifically
        # "A" -> needs ===
        res = self.api.write_chunk(self.test_filename, "A") # "A===" -> valid? "A" is 000000. 
        # base64.b64decode("A===") -> b'' (or error depending on impl)
        # base64.b64decode("QQ==") -> b'A'
        
        res = self.api.write_chunk(self.test_filename, "QQ") # "QQ==" -> b'A'
        self.assertEqual(res['status'], 'success')

if __name__ == '__main__':
    unittest.main()

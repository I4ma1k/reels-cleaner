import os
import sys
import subprocess
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_home_page():
    print("Testing GET / ...")
    response = client.get("/")
    assert response.status_code == 200
    assert "ReelCleaner" in response.text
    print("✓ Home page loaded successfully!")

def test_network_info():
    print("Testing GET /api/network-info ...")
    response = client.get("/api/network-info")
    assert response.status_code == 200
    data = response.json()
    assert "local_ip" in data
    assert "qr_b64" in data
    print(f"✓ Network info: IP={data['local_ip']}, Port={data['port']}")

def test_process_url():
    print("Testing POST /api/process-url with DFqWV3JN6Mj ...")
    url = "https://www.instagram.com/reel/DFqWV3JN6Mj/"
    response = client.post("/api/process-url", json={
        "url": url,
        "trim_end": 3.0,
        "auto_trim": True
    })
    print("Status code:", response.status_code)
    assert response.status_code == 200
    data = response.json()
    print("Response data:", data)
    assert data["status"] == "success"
    assert data["seconds_removed"] == 3.0
    assert data["clean_duration"] < data["original_duration"]
    print(f"✓ Original: {data['original_duration']}s -> Clean: {data['clean_duration']}s (-{data['seconds_removed']}s)")

    # Test download endpoint
    file_id = data["file_id"]
    dl_response = client.get(f"/api/download/{file_id}")
    assert dl_response.status_code == 200
    assert len(dl_response.content) > 1000
    print(f"✓ Download endpoint returned {len(dl_response.content)} bytes")

def test_process_upload():
    print("Testing POST /api/process-upload ...")
    # Generate a dummy 6-second mp4 using ffmpeg
    test_dummy = "test_dummy_upload.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=duration=6:size=320x240:rate=30",
        "-f", "lavfi", "-i", "sine=frequency=1000:duration=6",
        "-c:v", "libx264", "-c:a", "aac", test_dummy
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    with open(test_dummy, "rb") as f:
        response = client.post(
            "/api/process-upload",
            files={"file": ("test_upload.mp4", f, "video/mp4")},
            data={"trim_end": "3.0", "auto_trim": "true"}
        )
    if os.path.exists(test_dummy):
        os.remove(test_dummy)

    print("Upload status code:", response.status_code)
    assert response.status_code == 200
    data = response.json()
    print("Upload response:", data)
    assert data["status"] == "success"
    assert data["seconds_removed"] == 3.0
    assert abs(data["clean_duration"] - 3.0) < 0.2
    print(f"✓ Upload trimmed accurately to {data['clean_duration']}s")

if __name__ == "__main__":
    test_home_page()
    test_network_info()
    test_process_upload()
    test_process_url()
    print("\n🎉 ALL TESTS PASSED SUCCESSFULLY!")

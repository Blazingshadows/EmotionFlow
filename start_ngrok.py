from pyngrok import ngrok

ngrok.set_auth_token("2vl5myVZk4x43iJosXlWExiquLm_A3554R3gXMsL8yukZe3J")

# Start ngrok tunnel
public_url = ngrok.connect(8888, "http")
print(f"Tunnel URL: {public_url}")
print("Keep this terminal open while running the app!")
input("Press Enter to stop...")
ngrok.kill()
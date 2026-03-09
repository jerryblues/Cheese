docker stop webrtc-stress
docker rm -f webrtc-stress
docker run -d --name webrtc-stress   --network host   -v $(pwd)/config.json:/app/config.json   mpromonet/webrtc-streamer -C /app/config.json -H 0.0.0.0:8001 -vvv

docker logs -f webrtc-stress

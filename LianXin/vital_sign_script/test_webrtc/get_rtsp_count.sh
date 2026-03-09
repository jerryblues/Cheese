# 查看流配置列表
# curl -s http://127.0.0.1:8001/api/getMediaList | jq
# 查看当前活跃连接数
curl -s http://127.0.0.1:8001/api/getPeerConnectionList | jq '. | length'
# 查看所有 PeerID
# curl -s http://127.0.0.1:8001/api/getPeerConnectionList | jq
# 查看 CPU/内存开销
# docker stats webrtc-stress


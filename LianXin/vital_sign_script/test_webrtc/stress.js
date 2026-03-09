const fetch = (...args) => import('node-fetch').then(({default: fetch}) => fetch(...args)).catch(() => require('node-fetch')(...args));

const SERVER_IP = "10.1.10.147";
const SERVER_PORT = "8001";
const STREAMER_URL = `http://${SERVER_IP}:${SERVER_PORT}`;
const GOLDEN_SDP = "v=0\r\no=- 12345 2 IN IP4 127.0.0.1\r\ns=-\r\nt=0 0\r\na=msid-semantic: WMS\r\nm=video 9 UDP/TLS/RTP/SAVPF 96\r\nc=IN IP4 0.0.0.0\r\na=rtcp:9 IN IP4 0.0.0.0\r\na=ice-ufrag:test\r\na=ice-pwd:testtesttesttesttesttest\r\na=fingerprint:sha-256 93:60:AB:95:AF:7E:3E:30:40:CF:B4:39:61:4C:C8:39:A0:22:B5:7F:E6:E0:6D:5B:B2:55:D9:66:C0:0C:D2:4E\r\na=setup:actpass\r\na=mid:0\r\na=recvonly\r\na=rtcp-mux\r\na=rtcp-rsize\r\na=rtpmap:96 VP8/90000\r\n";

async function main() {
    try {
        const res = await fetch(`${STREAMER_URL}/api/getMediaList`);
        const mediaData = await res.json();
        
        // 1. 获取所有包含 video 的流名称（如 cam01, cam02...）
        const streams = mediaData.filter(item => item && item.video).map(item => item.video);

        console.log(`Node.js: 检测到 ${streams.length} 路流，开始发送 TCP 请求...`);

        for (let i = 0; i < streams.length; i++) {
            const streamName = streams[i];
            const peerId = `0.stress_${i}_${Math.random().toString().substring(2,7)}`;
            
            // 2. 关键修改点：在 URL 后增加 options=rtptransport%3Dtcp 强制走 TCP
            // 注意：webrtc-streamer 会透传这个参数给后端的 RTSP 拉流和 WebRTC 传输
            const callUrl = `${STREAMER_URL}/api/call?url=${encodeURIComponent(streamName)}&peerid=${peerId}&options=rtptransport%3Dtcp`;

            fetch(callUrl, {
                method: 'POST',
                body: JSON.stringify({ type: "offer", sdp: GOLDEN_SDP }),
                headers: { 'Content-Type': 'application/json' }
            }).catch((err) => console.error(`请求失败: ${streamName}`, err.message));
            
            // 保持 200ms 间隔，避免瞬时并发过高导致 Kylin 内核丢包
            await new Promise(r => setTimeout(r, 200)); 
        }
        console.log("Node.js: 所有 Offer (TCP 模式) 指令已发出。");
    } catch (e) {
        console.error("Node.js 运行出错:", e.message);
    }
}

main();

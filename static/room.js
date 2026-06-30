// 色スウォッチ描画: HEXコードを色四角付きに変換
function renderColorSwatches(text){
  if(!text || typeof text !== 'string') return text;
  return text.replace(/#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})\b/g, function(hex){
    return hex + '<span style="display:inline-block;width:16px;height:16px;background:' + hex + ';border:1px solid #555;border-radius:3px;vertical-align:middle;margin:0 4px;box-shadow:0 1px 2px rgba(0,0,0,0.3);"></span>';
  });
}

// ====================================================
// ナナチの部屋 v3.1 — スライドイン/アウト + 表情切替 + VOICEVOX
// ====================================================

const API_URL = "/api/chat";
const TTS_URL = "/tts/voicevox";
const LANG = "ja-JP";
const SESSION_ID = "room_" + Math.random().toString(36).slice(2, 10);
const EXPRESSIONS = ["normal", "smile", "think", "surprise", "wink", "sleepy", "smug"];

// VOICEVOX speaker ID【要確認】
// 3=ずんだもん / 20=もち子さん(ノーマル) ※環境による
const TTS_SPEAKER = 20;
const TTS_ENABLED = true;
const TTS_MAX_LEN = 200;

// ---------- 要素取得 ----------
const speechBubble  = document.getElementById("speechBubble");
const speechText    = document.getElementById("speechText");
const chatPanel     = document.getElementById("chatPanel");
const chatLauncher  = document.getElementById("chatLauncher");
const chatClose     = document.getElementById("chatClose");
const chatLog       = document.getElementById("chatLog");
const chatInput     = document.getElementById("chatInput");
const sendBtn       = document.getElementById("sendBtn");
const micBtn        = document.getElementById("micBtn");
const chatStatus    = document.getElementById("chatStatus");
const particlesEl   = document.getElementById("particles");
const nanachiWrap   = document.getElementById("nanachiWrap");

// ---------- TTS ----------
let currentAudio = null;
async function playTTS(text) {
  if (!TTS_ENABLED || !text) return;
  // 前の再生を止める
  if (currentAudio) {
    try { currentAudio.pause(); currentAudio.src = ""; } catch(e){}
    currentAudio = null;
  }
  // 長文切り詰め
  const cleanText = text.replace(/[🐰😊🤔😲😏😴😉⁉️【】\[\]]/g, "").trim();
  const speak = cleanText.length > TTS_MAX_LEN
    ? cleanText.slice(0, TTS_MAX_LEN) + "、以下省略だぜ"
    : cleanText;
  if (!speak) return;
  try {
    const url = `${TTS_URL}?text=${encodeURIComponent(speak)}&speaker=${TTS_SPEAKER}`;
    const audio = new Audio(url);
    currentAudio = audio;
    audio.onerror = (e) => {
      console.warn("🔇 TTS再生エラー(無音フォールバック):", e);
      currentAudio = null;
    };
    audio.onended = () => { currentAudio = null; };
    await audio.play().catch(err => {
      console.warn("🔇 TTS play失敗(autoplayブロック?):", err);
    });
  } catch (err) {
    console.warn("🔇 TTS要求失敗:", err);
  }
}

// ---------- チャット開閉 ----------
function openChat() {
  document.body.classList.add("chat-open");
  setTimeout(() => chatInput.focus(), 350);
}
function closeChat() {
  document.body.classList.remove("chat-open");
  chatInput.blur();
}
chatLauncher.addEventListener("click", openChat);
chatClose.addEventListener("click", closeChat);

document.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !document.body.classList.contains("chat-open")) {
    const tag = (document.activeElement && document.activeElement.tagName) || "";
    if (tag !== "INPUT" && tag !== "TEXTAREA") {
      e.preventDefault();
      openChat();
    }
  }
  if (e.key === "Escape" && document.body.classList.contains("chat-open")) {
    closeChat();
  }
});

// ---------- 表情切替 ----------
let currentExpr = "normal";
function setExpression(name, holdMs = 0) {
  if (!EXPRESSIONS.includes(name)) name = "normal";
  document.querySelectorAll(".nanachi-face").forEach(img => {
    if (img.dataset.expr === name) img.classList.add("active");
    else img.classList.remove("active");
  });
  currentExpr = name;
  if (holdMs > 0 && name !== "normal") {
    setTimeout(() => setExpression("normal"), holdMs);
  }
}

// ---------- 瞬き ----------
function blink() {
  const activeImg = document.querySelector(".nanachi-face.active");
  if (activeImg && currentExpr === "normal") {
    activeImg.classList.add("blink");
    setTimeout(() => activeImg.classList.remove("blink"), 200);
  }
  setTimeout(blink, 3000 + Math.random() * 3500);
}
setTimeout(blink, 2500);

// ---------- 表情推定 ----------
function inferExpressionFromText(text) {
  if (!text) return "normal";
  if (/(嬉し|たのし|楽し|やった|よかった|いいぜ|🐰|☺|😊|笑)/.test(text)) return "smile";
  if (/(困|分から|わから|どうし|うーん|ふむ|考え|難し|🤔|【要確認】)/.test(text)) return "think";
  if (/(え！|えっ|まじ|本当|ほんと|なんだと|びっく|驚|！！|？！|😲|⁉)/.test(text)) return "surprise";
  if (/(完璧|完全|当然|余裕|簡単|任せ|オイラの|決まり|確定|😏)/.test(text)) return "smug";
  if (/(眠|疲れ|ふにゃ|ねむ|だる|😴)/.test(text)) return "sleepy";
  if (/(任せろ|よろし|頼む|まかせ|😉)/.test(text.slice(-30))) return "wink";
  return "normal";
}

// ---------- パーティクル ----------
function spawnParticle() {
  const p = document.createElement("div");
  p.className = "particle";
  const startX = Math.random() * window.innerWidth;
  const dx = (Math.random() - 0.5) * 200;
  const dur = 8 + Math.random() * 10;
  const size = 2 + Math.random() * 5;
  p.style.left = startX + "px";
  p.style.bottom = "-10px";
  p.style.width = size + "px";
  p.style.height = size + "px";
  p.style.setProperty("--dx", dx + "px");
  p.style.animationDuration = dur + "s";
  particlesEl.appendChild(p);
  setTimeout(() => p.remove(), dur * 1000);
}
setInterval(spawnParticle, 900);
for (let i = 0; i < 6; i++) setTimeout(spawnParticle, i * 250);

// ---------- 台詞バブル ----------
let bubbleTimer = null;
function showSpeech(text, holdMs = 4500) {
  speechText.textContent = text;
  speechBubble.classList.add("show");
  if (bubbleTimer) clearTimeout(bubbleTimer);
  bubbleTimer = setTimeout(() => speechBubble.classList.remove("show"), holdMs);
}

// ---------- 初回挨拶 ----------
const greetings = [
  { text: "んなぁ～、よく来たな、りょーご🐰", expr: "smile" },
  { text: "オイラの部屋へようこそだぜ", expr: "wink" },
  { text: "暖炉の前で話そうぜ。Enterキー押すかアイコンタップで話せるぜ", expr: "smile" },
  { text: "星が綺麗な夜だぜ。今日は何を聞きたい？", expr: "normal" }
];
setTimeout(() => {
  const g = greetings[Math.floor(Math.random() * greetings.length)];
  showSpeech(g.text, 5500);
  setExpression(g.expr, 4500);
  // 初回挨拶もTTSで読む（autoplay制限でブロックされる可能性あり）
  playTTS(g.text);
}, 800);

// ---------- ホットスポット ----------
const hotspotReactions = {
  window:     { msg: "星空を眺めてるとな、奈落の底を思い出すんだぜ…", expr: "sleepy" },
  fireplace:  { msg: "暖炉の火、見てると落ち着くだろ？オイラもだぜ🐰", expr: "smile" },
  bookshelf:  { msg: "この本棚にはお前の簿記資料も入ってんだぜ。RAGってやつだな", expr: "smug" }
};
document.querySelectorAll(".hotspot").forEach(el => {
  el.addEventListener("click", () => {
    const r = hotspotReactions[el.dataset.area];
    if (r) {
      showSpeech(r.msg, 4000);
      setExpression(r.expr, 3500);
      playTTS(r.msg);
    }
  });
});

// ---------- ナナチクリック ----------
const tapReactions = [
  { msg: "ふにゃ、なに触ってんだよ", expr: "surprise" },
  { msg: "んなぁ、撫でるな撫でるな🐰", expr: "wink" },
  { msg: "話したきゃ左のアイコンタップしろ", expr: "smug" },
  { msg: "尻尾は別料金だぜ", expr: "smug" },
  { msg: "ふにゃぁ…眠かったのに…", expr: "sleepy" },
  { msg: "なんだよぉ、忙しいのに", expr: "think" }
];
nanachiWrap.addEventListener("click", () => {
  const r = tapReactions[Math.floor(Math.random() * tapReactions.length)];
  showSpeech(r.msg, 3500);
  setExpression(r.expr, 3000);
  playTTS(r.msg);
});

// ---------- メッセージ送信 ----------
function appendMsg(role, text) {
  const div = document.createElement("div");
  div.className = "msg-" + role;
  // IMGCARDパーサー: [IMGCARD:タイトル|画像URL|参照URL] をサムネカードに変換
        const imgcardRe = /\[IMGCARD:([^|\]]+)\|([^|\]]+)\|([^\]]+)\]/g;
const swatchRe = /\[SWATCH:([^|\]]+)\|([^|\]]+)(?:\|([^\]]+))?\]/g;
// SWATCH パース処理を IMGCARD の後に追加
const swatchParts = [];
let swatchLastIdx = 0;
let sm;
while ((sm = swatchRe.exec(text)) !== null) {
    if (sm.index > swatchLastIdx) {
        swatchParts.push({type:'text', content: text.slice(swatchLastIdx, sm.index)});
    }
    swatchParts.push({type:'swatch', hex: sm[1].trim(), name: sm[2].trim(), ratio: (sm[3]||'').trim()});
    swatchLastIdx = sm.index + sm[0].length;
}

        const parts = [];
        let lastIdx = 0;
        let m;
        while ((m = imgcardRe.exec(text)) !== null) {
            if (m.index > lastIdx) {
                parts.push({type: 'text', content: text.slice(lastIdx, m.index)});
            }
            parts.push({type: 'imgcard', title: m[1].trim(), imgUrl: m[2].trim(), srcUrl: m[3].trim()});
            lastIdx = m.index + m[0].length;
        }
        if (lastIdx < text.length) {
            parts.push({type: 'text', content: text.slice(lastIdx)});
        }
        if (parts.length === 0) {
            parts.push({type: 'text', content: text});
        }

        parts.forEach(part => {
            if (part.type === 'text') {
                const span = document.createElement('span');
                span.style.whiteSpace = 'pre-wrap';
                span.innerHTML = renderMarkdownLite(part.content);
                div.appendChild(span);
            } else {
                const card = document.createElement('div');
                card.className = 'imgcard';
                card.title = part.title + ' (クリックで拡大)';
                card.addEventListener('click', (e) => {
                    e.preventDefault();
                    openLightbox(part.imgUrl, part.title, part.srcUrl);
                });
                const img = document.createElement('img');
                img.src = part.imgUrl;
                img.alt = part.title;
                img.loading = 'lazy';
                img.onerror = () => { img.style.display = 'none'; card.textContent = '🖼️ ' + part.title; };
                const cap = document.createElement('div');
                cap.className = 'imgcard-caption';
                cap.textContent = part.title;
                card.appendChild(img);
                card.appendChild(cap);
                div.appendChild(card);
            }
        });
        // [SWATCH:#HEX|色名|比率] チップ描画
        swatchParts.forEach(p => {
            if (p.type === 'swatch') {
                const chip = document.createElement('span');
                chip.className = 'swatch-chip';
                chip.style.background = p.hex;
                const pct = p.ratio ? ' (' + Math.round(parseFloat(p.ratio) * 100) + '%)' : '';
                chip.title = p.name + ' ' + p.hex + pct + ' — クリックでコピー';
                chip.onclick = () => {
                    navigator.clipboard.writeText(p.hex);
                    chip.classList.add('copied');
                    setTimeout(() => chip.classList.remove('copied'), 1000);
                };
                const label = document.createElement('span');
                label.className = 'swatch-chip-label';
                label.textContent = p.hex;
                chip.appendChild(label);
                div.appendChild(chip);
            }
        });
  chatLog.appendChild(div);
  chatLog.scrollTop = chatLog.scrollHeight;
}

async function sendMessage(text) {
  if (!text || !text.trim()) return;
  appendMsg("user", text);
  chatInput.value = "";
  chatStatus.textContent = "ナナチ思考中…";
  showSpeech("ふむ、ちょっと考えるぜ…", 2500);
  setExpression("think");

  setTimeout(() => closeChat(), 1200);

  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({message: text, session_id: SESSION_ID})
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    // SSEストリーム読み取り (ハートビートをスキップして data: 行を解析)
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const {done, value} = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, {stream: true});
      const chunks = buffer.split("\n\n");
      buffer = chunks.pop() ?? "";
      for (const chunk of chunks) {
        const line = chunk.trim();
        if (!line || line.startsWith(":")) continue; // ハートビートをスキップ
        if (line.startsWith("data: ")) {
          const data = JSON.parse(line.slice(6));
          const reply = data.reply || data.answer || data.response || JSON.stringify(data);
          appendMsg("nanachi", reply);
          const expr = inferExpressionFromText(reply);
          setExpression(expr, 8000);
          const short = reply.length > 90 ? reply.slice(0, 88) + "…" : reply;
          showSpeech(short, 8000);
          chatStatus.textContent = "準備OK";
          if (data.mode && window.applyNanachiMode) window.applyNanachiMode(data.mode);
          // ★ VOICEVOX 自動再生
          playTTS(reply);
        }
      }
    }
  } catch (err) {
    appendMsg("nanachi", "んなぁ、通信失敗だぜ… " + err.message);
    showSpeech("通信失敗…", 3000);
    setExpression("surprise", 2500);
    chatStatus.textContent = "エラー: " + err.message;
  }
}

sendBtn.addEventListener("click", () => sendMessage(chatInput.value));
chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage(chatInput.value);
  }
});

// ---------- 音声入力 ----------
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;
if (SR) {
  recognition = new SR();
  recognition.lang = LANG;
  recognition.interimResults = false;
  recognition.continuous = false;
  recognition.onresult = (e) => {
    const text = e.results[0][0].transcript;
    chatInput.value = text;
    sendMessage(text);
  };
  recognition.onerror = (e) => {
    chatStatus.textContent = "STTエラー: " + e.error;
    showSpeech("んなぁ、聞き取れなかったぜ…", 3000);
    setExpression("think", 2500);
  };
  recognition.onend = () => micBtn.textContent = "🎙️";
  micBtn.addEventListener("click", () => {
    try {
      recognition.start();
      micBtn.textContent = "🔴";
      chatStatus.textContent = "聞いてる…";
      showSpeech("ん、話せ", 2000);
      setExpression("surprise", 1500);
    } catch (err) {
      chatStatus.textContent = "STT開始失敗: " + err.message;
    }
  });
} else {
  micBtn.style.opacity = 0.4;
  micBtn.title = "このブラウザは音声入力非対応";
}

console.log("🐰 ナナチの部屋 v3.1 起動完了 / session=" + SESSION_ID);
console.log("🔊 VOICEVOX speaker=" + TTS_SPEAKER + " / enabled=" + TTS_ENABLED);

// ====================================================
// 自動モード切替システム（v14.1・背景画像切替対応）
// ====================================================

window.nanachiCurrentMode = "normal";

// bgImage: 既存アセットで仮実装。本番画像(assets/rooms/)配置後に差し替え
// === v14.3: MODE_CONFIG 完全版（背景画像 + キャラ画像対応） ===
const MODE_CONFIG = {
  "normal": {
    msg: "🐰 リビングでまったり話そうな",
    color: "#2a1810",
    emoji: "🛋️",
    character: "/ui/assets/expressions/nanachi_neutral.png",
    bgImage: "/ui/assets/rooms/room_normal.jpg"
  },
  "bookkeeping": {
    msg: "🐰 眼鏡かけて書斎に移ったぞ",
    color: "#1a2030",
    emoji: "📚",
    character: "/ui/assets/expressions/nanachi_serious.png",
    bgImage: "/ui/assets/rooms/room_bookkeeping.jpg"
  },
  // "legal": v15.0で削除（応答速度最優先・ChromaDBデータは保護済み）
  "code": {
    msg: "🐰 ヘッドフォン装着で開発部屋に来たぞ",
    color: "#181818",
    emoji: "💻",
    character: "/ui/assets/expressions/nanachi_absorbed.png",
    bgImage: "/ui/assets/rooms/room_code.jpg"
  }
};

// === v14.3: 感情系表情（モード非依存） ===
const EMOTION_CHARACTERS = {
  smile:    "/ui/assets/expressions/nanachi_smile.png",
  troubled: "/ui/assets/expressions/nanachi_troubled.png"
};

// [v14.3 dedupe] 旧 applyNanachiMode (v14.1) 削除済み


window.applyNanachiMode = function(newMode) {
  if (!newMode || newMode === window.nanachiCurrentMode) return;
  const oldMode = window.nanachiCurrentMode;
  window.nanachiCurrentMode = newMode;
  console.log("[Auto-Mode] " + oldMode + " → " + newMode);

  const cfg = MODE_CONFIG[newMode] || MODE_CONFIG["normal"];

  // 背景画像切替（.room-bg 要素のフェード）
  var roomBg = document.querySelector(".room-bg");
  if (roomBg) {
    roomBg.style.opacity = "0";
    setTimeout(function() {
      roomBg.style.backgroundImage = "url('" + cfg.bgImage + "')";
      roomBg.style.opacity = "1";
    }, 400);
  }

  // キャラ表情切替（モードに対応した表情に）
  if (typeof setExpression === "function") {
    setExpression(cfg.charExpr, 0);
  }

  // モード遷移通知
  _showModeNotification("🐰 " + cfg.msg);
  _updateModeBadge(newMode, cfg.emoji);
};

function _showModeNotification(msg) {
  const notif = document.createElement("div");
  notif.textContent = msg;
  notif.style.cssText =
    "position:fixed;top:30%;left:50%;transform:translate(-50%,-50%);" +
    "background:rgba(40,30,20,0.95);color:#d4a574;padding:14px 22px;" +
    "border-radius:10px;border:2px solid #d4a574;font-size:14px;" +
    "font-family:sans-serif;z-index:10000;box-shadow:0 4px 20px rgba(0,0,0,0.5);" +
    "animation:modeNotifFade 2.5s ease-in-out;pointer-events:none;";
  document.body.appendChild(notif);
  setTimeout(function() { notif.remove(); }, 2600);
}

function _updateModeBadge(mode) {
  // v14.1: モードバッジ削除（既存要素があれば除去）
  try {
    var existing = document.getElementById('nanachi-mode-badge');
    if (existing && existing.parentNode) existing.parentNode.removeChild(existing);
  } catch(e) {}
}

// CSSアニメーション注入
(function() {
  if (document.getElementById("mode-anim-css")) return;
  const s = document.createElement("style");
  s.id = "mode-anim-css";
  s.textContent =
    "@keyframes modeNotifFade{" +
    "0%{opacity:0;transform:translate(-50%,-60%)}" +
    "15%{opacity:1;transform:translate(-50%,-50%)}" +
    "85%{opacity:1;transform:translate(-50%,-50%)}" +
    "100%{opacity:0;transform:translate(-50%,-40%)}}";
  document.head.appendChild(s);
})();

// fetchインターセプタ: SSEストリームは clone().json() 不可のためスキップ
// mode 更新は sendMessage の SSE ハンドラ内で直接 applyNanachiMode を呼ぶ
(function() {
  const _origFetch = window.fetch;
  window.fetch = function(url, opts) {
    return _origFetch.call(this, url, opts).then(function(resp) {
      if (typeof url === "string" && url.includes("/api/chat")) {
        const ct = resp.headers.get("content-type") || "";
        if (!ct.includes("text/event-stream")) {
          resp.clone().json().then(function(data) {
            if (data && data.mode) window.applyNanachiMode(data.mode);
          }).catch(function() {});
        }
      }
      return resp;
    });
  };
})();

// 初期バッジ表示
window.addEventListener("DOMContentLoaded", function() {
  _updateModeBadge("normal", "🛋️");
});
_updateModeBadge("normal", "🛋️");

console.log("[Auto-Mode System v14.1] initialized");

// === v14.1: マークダウン簡易レンダラ ===
// コードブロック / テーブル / 太字 / リスト / 改行 を最小限処理
window.renderMarkdownLite = function(text) {
  if (!text) return '';
  var html = text;

  // 1. HTMLエスケープ（XSS対策）
  html = html.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

  // 2. コードブロック ```...```
  html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, function(_, lang, code) {
    return '<pre style="background:#1a1a1a;color:#e0e0e0;padding:8px;border-radius:4px;overflow-x:auto;font-family:monospace;font-size:0.9em;">' + code + '</pre>';
  });

  // 3. テーブル | a | b | c |
  // 簡易検出: 連続する | で始まり | で終わる行
  var lines = html.split('\n');
  var inTable = false;
  var tableBuffer = [];
  var out = [];
  for (var i = 0; i < lines.length; i++) {
    var line = lines[i];
    if (/^\s*\|.*\|\s*$/.test(line)) {
      // テーブル行
      if (!inTable) { inTable = true; tableBuffer = []; }
      // 区切り行 |---|---| はスキップ
      if (/^\s*\|[\s\-:|]+\|\s*$/.test(line)) continue;
      var cells = line.split('|').slice(1, -1).map(function(s){return s.trim();});
      tableBuffer.push(cells);
    } else {
      if (inTable && tableBuffer.length > 0) {
        // テーブル終端 → HTML生成
        var tableHtml = '<table style="border-collapse:collapse;margin:8px 0;font-size:0.95em;">';
        for (var r = 0; r < tableBuffer.length; r++) {
          var tag = (r === 0) ? 'th' : 'td';
          tableHtml += '<tr>';
          for (var col = 0; col < tableBuffer[r].length; col++) {
            tableHtml += '<' + tag + ' style="border:1px solid #888;padding:4px 8px;">' + tableBuffer[r][col] + '</' + tag + '>';
          }
          tableHtml += '</tr>';
        }
        tableHtml += '</table>';
        out.push(tableHtml);
        inTable = false;
        tableBuffer = [];
      }
      out.push(line);
    }
  }
  // 最後がテーブルで終わる場合
  if (inTable && tableBuffer.length > 0) {
    var tableHtml = '<table style="border-collapse:collapse;margin:8px 0;font-size:0.95em;">';
    for (var r = 0; r < tableBuffer.length; r++) {
      var tag = (r === 0) ? 'th' : 'td';
      tableHtml += '<tr>';
      for (var col = 0; col < tableBuffer[r].length; col++) {
        tableHtml += '<' + tag + ' style="border:1px solid #888;padding:4px 8px;">' + tableBuffer[r][col] + '</' + tag + '>';
      }
      tableHtml += '</tr>';
    }
    tableHtml += '</table>';
    out.push(tableHtml);
  }
  html = out.join('\n');

  // 4. インラインコード `...`
  html = html.replace(/`([^`\n]+)`/g, '<code style="background:#2a2a2a;color:#e0e0e0;padding:1px 4px;border-radius:3px;font-family:monospace;font-size:0.9em;">$1</code>');

  // 5. 太字 **...**
  html = html.replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>');

  // 6. リスト - ... または * ...
  html = html.replace(/^\s*[-*]\s+(.+)$/gm, '<li style="margin-left:1.5em;">$1</li>');

  // 7. 改行 → <br>
  html = html.replace(/\n/g, '<br>');

    html = renderColorSwatches(html);
  return html;
};

console.log('[v14.1] renderMarkdownLite loaded');

// ===== Lightbox機能 =====
function openLightbox(imgUrl, title, srcUrl) {
    const existing = document.getElementById('lightbox-overlay');
    if (existing) existing.remove();
    const overlay = document.createElement('div');
    overlay.id = 'lightbox-overlay';
    overlay.className = 'lightbox-overlay';
    const container = document.createElement('div');
    container.className = 'lightbox-container';
    const img = document.createElement('img');
    img.src = imgUrl;
    img.alt = title;
    img.className = 'lightbox-image';
    const caption = document.createElement('div');
    caption.className = 'lightbox-caption';
    caption.textContent = title;
    if (srcUrl) {
        const linkBtn = document.createElement('a');
        linkBtn.href = srcUrl;
        linkBtn.target = '_blank';
        linkBtn.rel = 'noopener noreferrer';
        linkBtn.className = 'lightbox-link';
        linkBtn.textContent = '🔗 元サイトを開く';
        linkBtn.addEventListener('click', (e) => e.stopPropagation());
        caption.appendChild(document.createElement('br'));
        caption.appendChild(linkBtn);
    }
    const closeBtn = document.createElement('div');
    closeBtn.className = 'lightbox-close';
    closeBtn.textContent = '✕';
    closeBtn.addEventListener('click', (e) => { e.stopPropagation(); closeLightbox(); });
    container.appendChild(img);
    container.appendChild(caption);
    container.appendChild(closeBtn);
    overlay.appendChild(container);
    overlay.addEventListener('click', (e) => { if (e.target === overlay) closeLightbox(); });
    document.addEventListener('keydown', lightboxKeyHandler);
    document.body.appendChild(overlay);
    setTimeout(() => overlay.classList.add('lightbox-open'), 10);
}
function closeLightbox() {
    const overlay = document.getElementById('lightbox-overlay');
    if (overlay) { overlay.classList.remove('lightbox-open'); setTimeout(() => overlay.remove(), 200); }
    document.removeEventListener('keydown', lightboxKeyHandler);
}
function lightboxKeyHandler(e) { if (e.key === 'Escape') closeLightbox(); }


// ============================================================
// 2026-06-30 追加: 組み合わせ提案結果のリッチ描画
// ============================================================
function renderComboPairs(pairsData, targetEl) {
  if (!pairsData || !Array.isArray(pairsData) || pairsData.length === 0) return;
  if (!targetEl) targetEl = document.querySelector('.chat-messages') || document.body;

  const wrap = document.createElement('div');
  wrap.className = 'combo-pairs-wrap';
  wrap.style.cssText = 'margin:12px 0;padding:12px;background:#1a1a2e;border-radius:10px;';

  pairsData.forEach((p, i) => {
    const row = document.createElement('div');
    row.style.cssText = 'display:flex;align-items:center;gap:10px;padding:10px;margin:6px 0;background:#2a2a3e;border-radius:8px;flex-wrap:wrap;';

    // 順位 & スコア
    const rank = document.createElement('div');
    rank.style.cssText = 'min-width:60px;text-align:center;font-weight:bold;color:#ffd700;';
    rank.innerHTML = `#${i+1}<br><span style="font-size:12px;color:#fff;">${p.best_match.score}点</span>`;
    row.appendChild(rank);

    // 生地1サムネ
    if (p.fabric1.image_b64) {
      const img1 = document.createElement('img');
      img1.src = 'data:image/jpeg;base64,' + p.fabric1.image_b64;
      img1.style.cssText = 'width:60px;height:60px;object-fit:cover;border-radius:6px;';
      img1.title = p.fabric1.display;
      row.appendChild(img1);
    }

    // 色1チップ
    const c1 = document.createElement('div');
    c1.style.cssText = `width:32px;height:32px;background:${p.best_match.color1.hex};border-radius:6px;border:2px solid #fff;`;
    c1.title = `${p.best_match.color1.name_jp} (${p.best_match.color1.hex})`;
    row.appendChild(c1);

    // 中央：×記号
    const x = document.createElement('span');
    x.textContent = '×';
    x.style.cssText = 'color:#888;font-size:18px;';
    row.appendChild(x);

    // 色2チップ
    const c2 = document.createElement('div');
    c2.style.cssText = `width:32px;height:32px;background:${p.best_match.color2.hex};border-radius:6px;border:2px solid #fff;`;
    c2.title = `${p.best_match.color2.name_jp} (${p.best_match.color2.hex})`;
    row.appendChild(c2);

    // 生地2サムネ
    if (p.fabric2.image_b64) {
      const img2 = document.createElement('img');
      img2.src = 'data:image/jpeg;base64,' + p.fabric2.image_b64;
      img2.style.cssText = 'width:60px;height:60px;object-fit:cover;border-radius:6px;';
      img2.title = p.fabric2.display;
      row.appendChild(img2);
    }

    // テキスト説明
    const txt = document.createElement('div');
    txt.style.cssText = 'flex:1;min-width:200px;color:#eee;font-size:13px;';
    txt.innerHTML = `<b>${p.fabric1.display}</b> × <b>${p.fabric2.display}</b><br>` +
                    `<span style="color:#aaa;">${p.best_match.type}</span><br>` +
                    `<span style="color:#ccc;font-size:11px;">${p.best_match.reason}</span>`;
    row.appendChild(txt);

    wrap.appendChild(row);
  });

  targetEl.appendChild(wrap);
}

// チャット応答内の pairs_data を自動検出して描画する場合は、
// チャット表示関数 (appendMessage 等) からこの関数を呼び出してくれ

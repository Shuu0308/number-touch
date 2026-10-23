from flask import Flask, jsonify, render_template_string, request
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import json
import threading
import os

app = Flask(__name__)

# 記録ファイルは app.py と同じフォルダに作成されます。
DATA_FILE = Path(__file__).with_name("records.sqlite3")

HTML = r"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>カラフル数字タッチ！</title>
    <style>
        :root {
            --ink: #342b5c;
            --muted: #756c93;
            --pink: #ff5ca8;
            --purple: #7657ff;
            --blue: #42b9f5;
            --yellow: #ffcf4a;
            --green: #3bd6a0;
            --panel: rgba(255, 255, 255, .88);
        }

        * { box-sizing: border-box; }
        button, select, input { touch-action: manipulation; }

        body {
            margin: 0;
            min-height: 100vh;
            padding: 28px 14px 40px;
            color: var(--ink);
            font-family: "Trebuchet MS", "Yu Gothic", Meiryo, sans-serif;
            background:
                radial-gradient(circle at 10% 8%, #ffd7eb 0, transparent 25%),
                radial-gradient(circle at 90% 12%, #c8f3ff 0, transparent 28%),
                radial-gradient(circle at 80% 90%, #e4d7ff 0, transparent 27%),
                linear-gradient(135deg, #fff8d8, #f7eaff 55%, #e4f9ff);
        }

        .app { width: min(100%, 820px); margin: 0 auto; }
        header { text-align: center; margin-bottom: 20px; }
        .eyebrow {
            display: inline-block; padding: 6px 13px; border-radius: 99px;
            background: #fff; color: #8b56d9; font-size: 12px; font-weight: 900;
            letter-spacing: 1.5px; box-shadow: 0 5px 18px #7150a31a;
        }
        h1 { margin: 12px 0 6px; font-size: clamp(30px, 6vw, 46px); line-height: 1.1; }
        h1 .rainbow {
            background: linear-gradient(90deg, #ff4fa0, #8657ff, #25bce9, #16bd8c);
            color: transparent; background-clip: text; -webkit-background-clip: text;
        }
        header p { margin: 0; color: var(--muted); font-weight: 600; }

        .panel {
            background: var(--panel); border: 2px solid #fff;
            border-radius: 24px; padding: 20px;
            box-shadow: 0 12px 35px #4c318c14;
            backdrop-filter: blur(8px);
        }

        .toolbar {
            display: flex; flex-wrap: wrap; gap: 12px;
            align-items: end; justify-content: space-between; margin-bottom: 16px;
        }
        .field { display: grid; gap: 6px; font-weight: 800; font-size: 13px; }
        select, input[type="number"], input[type="text"] {
            min-height: 42px; border: 2px solid #e9e1ff; border-radius: 12px;
            padding: 8px 12px; background: white; color: var(--ink);
            font: inherit; font-weight: 700;
        }
        .toggle {
            display: flex; align-items: center; gap: 8px; min-height: 42px;
            font-size: 14px; font-weight: 800;
        }
        .toggle input { width: 18px; height: 18px; accent-color: var(--purple); }

        .stats {
            display: grid; grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 10px; margin-bottom: 16px;
        }
        .stat {
            text-align: center; padding: 12px 8px; border-radius: 18px;
            background: #fff; border: 2px solid #f0eaff;
        }
        .stat:nth-child(1) { border-bottom: 4px solid var(--pink); }
        .stat:nth-child(2) { border-bottom: 4px solid var(--blue); }
        .stat:nth-child(3) { border-bottom: 4px solid var(--green); }
        .stat-label { font-size: 12px; font-weight: 800; color: var(--muted); }
        .stat-value { font-size: clamp(19px, 4vw, 28px); font-weight: 900; margin-top: 3px; }
        .stat-value small { font-size: 12px; }

        #board {
            width: min(100%, 510px); margin: 0 auto;
            display: grid; gap: clamp(5px, 1.6vw, 10px);
        }
        .cell {
            position: relative; aspect-ratio: 1 / 1; min-width: 0;
            border: 0; border-radius: clamp(9px, 2vw, 18px);
            background: white; color: #453663;
            box-shadow: 0 5px 0 #dcd2f3, 0 7px 14px #55428a14;
            font-size: clamp(17px, 4.6vw, 31px); font-weight: 900;
            cursor: pointer; transition: transform .12s, box-shadow .12s, background .12s;
            -webkit-tap-highlight-color: transparent;
        }
        .cell:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 7px 0 #dcd2f3, 0 10px 16px #55428a1c; }
        .cell:active:not(:disabled) { transform: translateY(3px); box-shadow: 0 2px 0 #dcd2f3; }
        .cell:focus-visible { outline: 4px solid #7657ff80; outline-offset: 2px; }
        .cell.done {
            background: linear-gradient(135deg, #b8f6d9, #75e9bd);
            color: #167a5b; box-shadow: 0 4px 0 #49c79b; cursor: default;
        }
        .cell.wrong { background: #ffd1df; color: #c02b66; animation: shake .18s linear; }
        .cell:disabled { cursor: default; }
        @keyframes shake { 25% { transform: translateX(-3px); } 75% { transform: translateX(3px); } }

        #message {
            min-height: 30px; margin: 16px 0 12px; text-align: center;
            color: #6f50c8; font-weight: 900; font-size: 16px;
        }
        .actions { display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; }
        .btn {
            border: 0; border-radius: 14px; padding: 12px 22px; min-height: 46px;
            font: inherit; font-weight: 900; cursor: pointer;
            transition: transform .12s, filter .12s;
        }
        .btn:hover { filter: brightness(1.04); transform: translateY(-1px); }
        .btn:active { transform: translateY(1px); }
        .btn-primary { color: white; background: linear-gradient(100deg, #ff5ca8, #875cff); box-shadow: 0 5px 0 #d7c5ff; }
        .btn-secondary { color: #5e4c91; background: #f0eaff; }
        .below { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 18px; }
        h2 { font-size: 19px; margin: 0 0 12px; }
        .record-line {
            display: flex; align-items: center; justify-content: space-between; gap: 8px;
            padding: 9px 0; border-bottom: 1px solid #eee8ff; font-weight: 800;
        }
        .record-line:last-child { border-bottom: 0; }
        .record-time { color: #6b4de1; font-variant-numeric: tabular-nums; }
        .empty { color: var(--muted); font-size: 14px; }
        .small-note { color: var(--muted); font-size: 12px; line-height: 1.6; margin: 10px 0 0; }
        .overlay {
            position: fixed; inset: 0; z-index: 10; display: flex;
            align-items: center; justify-content: center; padding: 20px;
            background: #2e205b75; backdrop-filter: blur(5px);
        }
        .overlay[hidden] { display: none; }
        .count-card {
            width: min(90vw, 360px); padding: 30px 20px; text-align: center;
            border: 4px solid white; border-radius: 28px; background: linear-gradient(145deg, #fff, #fff0fa);
            box-shadow: 0 20px 70px #24174b45;
        }
        #count-number {
            font-size: clamp(70px, 20vw, 110px); line-height: 1;
            font-weight: 1000; color: #ff54a3; text-shadow: 4px 4px 0 #ffd1e7;
        }
        #count-label { margin-top: 12px; font-size: 17px; font-weight: 900; }
        footer { text-align: center; color: #857a9e; font-size: 12px; margin-top: 18px; }

        @media (max-width: 600px) {
            body { padding: 18px 10px 28px; }
            .panel { padding: 13px; border-radius: 20px; }
            .toolbar { align-items: stretch; }
            .field { flex: 1; }
            .below { grid-template-columns: 1fr; }
            .stats { gap: 6px; }
            .stat { padding: 10px 4px; border-radius: 13px; }
            .btn { flex: 1; padding: 12px 10px; min-height: 48px; }
            .cell { user-select: none; -webkit-user-select: none; }
            header p { font-size: 14px; }
        }
    </style>
</head>
<body>
<div class="app">
    <header>
        <span class="eyebrow">QUICK • FOCUS • FUN</span>
        <h1><span class="rainbow">数字タッチ！</span> ✨</h1>
        <p>数字を見つけて、1から順番にタッチしよう！</p>
    </header>

    <main>
        <section class="panel">
            <div class="toolbar">
                <label class="field">プレイヤー名（ランキング表示）
                    <input id="player-name" type="text" maxlength="16" placeholder="ニックネーム" autocomplete="nickname">
                </label>
                <label class="field">ゲームモード
                    <select id="game-mode">
                        <option value="numbers">🔢 数字タッチ</option>
                        <option value="eras">📜 元号タッチ</option>
                    </select>
                </label>
                <label class="field">難易度
                    <select id="difficulty">
                        <option value="3">🌱 かんたん（3×3）</option>
                        <option value="4">⭐ ふつう（4×4）</option>
                        <option value="5" selected>🔥 むずかしい（5×5）</option>
                    </select>
                </label>
                <label class="field">ミスペナルティ
                    <select id="penalty">
                        <option value="0">なし</option>
                        <option value="1" selected>＋1秒</option>
                        <option value="3">＋3秒</option>
                        <option value="5">＋5秒</option>
                    </select>
                </label>
                <label class="toggle"><input type="checkbox" id="sound" checked> 🔊 効果音</label>
            </div>

            <div class="stats">
                <div class="stat">
                    <div class="stat-label">NEXT 🎯</div>
                    <div class="stat-value" id="next">1</div>
                </div>
                <div class="stat">
                    <div class="stat-label">TIME ⏱️</div>
                    <div class="stat-value"><span id="time">0.00</span><small> 秒</small></div>
                </div>
                <div class="stat">
                    <div class="stat-label">BEST 🏆</div>
                    <div class="stat-value"><span id="best">--</span><small id="best-unit"></small></div>
                </div>
            </div>

            <div id="board" aria-label="数字のボード"></div>
            <div id="message" role="status">スタートを押して挑戦しよう！</div>
            <div class="actions">
                <button class="btn btn-primary" id="start">▶ スタート</button>
                <button class="btn btn-secondary" id="reset">↻ シャッフル</button>
                <button class="btn btn-secondary" id="share" disabled>𝕏 結果をシェア</button>
            </div>
            <p class="small-note">間違えると設定した秒数が加算されます。ランキングに記録するにはニックネームを入力してね。公開サイトでは全国のプレイヤーと記録を共有します。</p>
        </section>

        <div class="below">
            <section class="panel">
                <h2>🏆 自己ベスト</h2>
                <div id="best-list" class="empty">記録を読み込み中...</div>
            </section>
            <section class="panel">
                <h2>🌏 全国ランキング TOP 10</h2>
                <div class="toolbar">
                    <label class="field">期間
                        <select id="ranking-period"><option value="all">総合</option><option value="day">今日</option><option value="week">今週</option></select>
                    </label>
                    <label class="field">難易度
                        <select id="ranking-size"><option value="5">5×5</option><option value="4">4×4</option><option value="3">3×3</option><option value="all">すべて</option></select>
                    </label>
                </div>
                <div id="ranking" class="empty">記録を読み込み中...</div>
            </section>
        </div>
    </main>
    <footer>ひとつずつ集中して、自己ベストを更新しよう！ 🌈</footer>
</div>

<div class="overlay" id="count-overlay" hidden>
    <div class="count-card">
        <div id="count-number">3</div>
        <div id="count-label">準備はいい？</div>
    </div>
</div>

<script>
    const board = document.getElementById("board");
    const difficulty = document.getElementById("difficulty");
    const gameMode = document.getElementById("game-mode");
    const eras = [
    "大化", "白雉", "朱鳥", "大宝", "慶雲", "和銅",
    "霊亀", "養老", "神亀", "天平", "天平感宝",
    "天平勝宝", "天平宝字", "天平神護", "神護景雲",
    "宝亀", "天応", "延暦", "大同", "弘仁",
    "天長", "承和", "嘉祥", "仁寿", "斉衡",
    "天安", "貞観", "元慶", "仁和", "寛平",
    "昌泰", "延喜", "延長", "承平", "天慶",
    "天暦", "天徳", "応和", "康保", "安和",
    "天禄", "天延", "貞元", "天元", "永観",
    "寛和", "永延", "永祚", "正暦", "長徳",
    "長保", "寛弘", "長和", "寛仁", "治安",
    "万寿", "長元", "長暦", "長久", "寛徳",
    "永承", "天喜", "康平", "治暦", "延久",
    "承保", "承暦", "永保", "応徳", "寛治",
    "嘉保", "永長", "承徳", "康和", "長治",
    "嘉承", "天仁", "天永", "永久", "元永",
    "保安", "天治", "大治", "天承", "長承",
    "保延", "永治", "康治", "天養", "久安",
    "仁平", "久寿", "保元", "平治", "永暦",
    "応保", "長寛", "永万", "仁安", "嘉応",
    "承安", "安元", "治承", "養和", "寿永",
    "元暦", "文治", "建久", "正治", "建仁",
    "元久", "建永", "承元", "建暦", "建保",
    "承久", "貞応", "元仁", "嘉禄", "安貞",
    "寛喜", "貞永", "天福", "文暦", "嘉禎",
    "暦仁", "延応", "仁治", "寛元", "宝治",
    "建長", "康元", "正嘉", "正元", "文応",
    "弘長", "文永", "建治", "弘安", "正応",
    "永仁", "正安", "乾元", "嘉元", "徳治",
    "延慶", "応長", "正和", "文保", "元応",
    "元亨", "正中", "嘉暦", "元徳",
    "元弘", "正慶", "建武", "延元", "暦応",
    "興国", "康永", "貞和", "正平", "観応",
    "文和", "延文", "康安", "貞治", "応安",
    "建徳", "文中", "天授", "永和", "弘和",
    "康暦", "永徳", "元中", "至徳", "嘉慶",
    "康応", "明徳", "応永", "正長", "永享",
    "嘉吉", "文安", "宝徳", "享徳", "康正",
    "長禄", "寛正", "文正", "応仁", "文明",
    "長享", "延徳", "明応", "文亀", "永正",
    "大永", "享禄", "天文", "弘治", "永禄",
    "元亀", "天正", "文禄", "慶長", "元和",
    "寛永", "正保", "慶安", "承応", "明暦",
    "万治", "寛文", "延宝", "天和", "貞享",
    "元禄", "宝永", "正徳", "享保", "元文",
    "寛保", "延享", "寛延", "宝暦", "明和",
    "安永", "天明", "寛政", "享和", "文化",
    "文政", "天保", "弘化", "嘉永", "安政",
    "万延", "文久", "元治", "慶応", "明治",
    "大正", "昭和", "平成", "令和"
];
    const penaltySelect = document.getElementById("penalty");
    const soundToggle = document.getElementById("sound");
    const nextDisplay = document.getElementById("next");
    const timeDisplay = document.getElementById("time");
    const bestDisplay = document.getElementById("best");
    const bestUnit = document.getElementById("best-unit");
    const message = document.getElementById("message");
    const startButton = document.getElementById("start");
    const resetButton = document.getElementById("reset");
    const shareButton = document.getElementById("share");
    let lastResult = null;
    const overlay = document.getElementById("count-overlay");
    const countNumber = document.getElementById("count-number");
    const countLabel = document.getElementById("count-label");

    let nextNumber = 1;
    let gameState = "ready"; // ready, countdown, playing, finished
    let startTime = 0;
    let elapsedBeforeFinish = 0;
    let penaltySeconds = 1;
    let tickTimer = null;
    let countdownTimer = null;
    let audioContext = null;
    let boardButtons = [];

    function getSize() {
        return Number(difficulty.value);
    }

    function getTotal() {
        return getSize() * getSize();
    }

    function getDifficultyLabel(size) {
        return `${size}×${size}`;
    }

    function stopTimers() {
        if (tickTimer !== null) {
            clearInterval(tickTimer);
            tickTimer = null;
        }
        if (countdownTimer !== null) {
            clearInterval(countdownTimer);
            countdownTimer = null;
        }
    }

    function getElapsed() {
        if (gameState === "playing") {
            return (Date.now() - startTime) / 1000;
        }
        return elapsedBeforeFinish;
    }

    function updateTime() {
        const elapsed = getElapsed();
        timeDisplay.textContent = elapsed.toFixed(2);
    }

    function playTone(frequency, duration, type = "sine", volume = 0.06) {
        if (!soundToggle.checked) return;
        try {
            const AudioContextClass = window.AudioContext || window.webkitAudioContext;
            if (!AudioContextClass) return;
            if (!audioContext) audioContext = new AudioContextClass();
            if (audioContext.state === "suspended") audioContext.resume();

            const oscillator = audioContext.createOscillator();
            const gain = audioContext.createGain();
            oscillator.type = type;
            oscillator.frequency.value = frequency;
            gain.gain.setValueAtTime(volume, audioContext.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + duration);
            oscillator.connect(gain);
            gain.connect(audioContext.destination);
            oscillator.start();
            oscillator.stop(audioContext.currentTime + duration);
        } catch (error) {
            // 音声が使えないブラウザでは、ゲーム自体はそのまま遊べます。
        }
    }

    function playCorrectSound() {
        playTone(660, 0.09, "sine", 0.045);
    }

    function playWrongSound() {
        playTone(190, 0.16, "triangle", 0.07);
    }

    function playClearSound() {
        playTone(523, 0.14, "sine", 0.06);
        setTimeout(() => playTone(659, 0.14, "sine", 0.06), 120);
        setTimeout(() => playTone(784, 0.22, "sine", 0.06), 240);
    }

    function setBoardEnabled(enabled) {
        boardButtons.forEach(button => {
            button.disabled = !enabled || button.classList.contains("done");
        });
    }

    function createBoard() {
        const total = getTotal();
        const numbers = Array.from({ length: total }, (_, i) => i + 1);

        // Fisher–Yates シャッフル：数字の順番をランダムにする
        for (let i = numbers.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [numbers[i], numbers[j]] = [numbers[j], numbers[i]];
        }

        board.innerHTML = "";
        board.style.gridTemplateColumns = `repeat(${getSize()}, minmax(0, 1fr))`;
        boardButtons = [];

        numbers.forEach(number => {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "cell";
            button.textContent = number;
            button.setAttribute("aria-label", `数字 ${number}`);
            button.disabled = true;
            button.addEventListener("click", () => handleNumberClick(number, button));
            board.appendChild(button);
            boardButtons.push(button);
        });
    }

    function resetGame() {
        stopTimers();
        gameState = "ready";
        nextNumber = 1;
        startTime = 0;
        elapsedBeforeFinish = 0;
        penaltySeconds = Number(penaltySelect.value);

        overlay.hidden = true;
        nextDisplay.textContent = "1";
        timeDisplay.textContent = "0.00";
        message.textContent = "スタートを押して挑戦しよう！";
        startButton.textContent = "▶ スタート";
        shareButton.disabled = true;
        lastResult = null;

        createBoard();
        loadRecords();
        updateBestDisplay();
    }

    function startCountdown() {
        stopTimers();
        gameState = "countdown";
        nextNumber = 1;
        elapsedBeforeFinish = 0;
        penaltySeconds = Number(penaltySelect.value);
        nextDisplay.textContent = "1";
        timeDisplay.textContent = "0.00";
        message.textContent = "カウントダウン中...";
        startButton.textContent = "▶ カウント中";
        setBoardEnabled(false);

        let count = 3;
        countNumber.textContent = count;
        countLabel.textContent = "準備はいい？";
        overlay.hidden = false;
        playTone(440, 0.1, "sine", 0.04);

        countdownTimer = setInterval(() => {
            count--;
            if (count > 0) {
                countNumber.textContent = count;
                countLabel.textContent = "集中して...！";
                playTone(440, 0.1, "sine", 0.04);
            } else {
                clearInterval(countdownTimer);
                countdownTimer = null;
                overlay.hidden = true;
                beginPlaying();
            }
        }, 1000);
    }

    function beginPlaying() {
        gameState = "playing";
        startTime = Date.now();
        elapsedBeforeFinish = 0;
        setBoardEnabled(true);
        startButton.textContent = "▶ プレイ中";
        message.textContent = "1から順番にタッチ！";
        tickTimer = setInterval(updateTime, 20);
    }

    function handleNumberClick(number, button) {
        if (gameState !== "playing") return;

        if (number === nextNumber) {
            button.classList.add("done");
            button.disabled = true;
            nextNumber++;
            nextDisplay.textContent = nextNumber > getTotal() ? "完了" : nextNumber;
            playCorrectSound();

            if (nextNumber > getTotal()) {
                finishGame();
            } else {
                message.textContent = `ナイス！ 次は ${nextNumber} ✨`;
            }
        } else {
            playWrongSound();
            elapsedBeforeFinish += penaltySeconds;
            // プレイ中の実時間にペナルティを加算するため、開始時刻を調整する
            startTime -= penaltySeconds * 1000;
            button.classList.add("wrong");
            message.textContent = penaltySeconds > 0
                ? `おっと！ ＋${penaltySeconds}秒のペナルティ 😵`
                : "おっと！ 次の数字を探そう 😵";
            setTimeout(() => button.classList.remove("wrong"), 220);
            updateTime();
        }
    }

    async function finishGame() {
        stopTimers();
        gameState = "finished";
        elapsedBeforeFinish = (Date.now() - startTime) / 1000;
        timeDisplay.textContent = elapsedBeforeFinish.toFixed(2);
        setBoardEnabled(false);
        startButton.textContent = "▶ もう一度遊ぶ";
        message.textContent = `🎉 クリア！ ${elapsedBeforeFinish.toFixed(2)} 秒！`;
        playClearSound();

        const playerName = playerNameInput.value.trim().slice(0, 16);
        const result = {
            size: getSize(),
            time: Number(elapsedBeforeFinish.toFixed(2)),
            player: playerName
        };
        lastResult = result;
        shareButton.disabled = false;
        if (!playerName) {
            message.textContent += " ニックネームを入力するとランキングに登録できるよ！";
        }

        try {
            const response = await fetch("/api/records", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(result)
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || "記録の保存に失敗しました");
            }
            const saved = await response.json();

            if (saved.is_best) {
                message.textContent += " 🏆 自己ベスト更新！";
            }
            await loadRecords();
            updateBestDisplay();
        } catch (error) {
            message.textContent += `（${error.message}）`;
        }
    }

    const rankingPeriod = document.getElementById("ranking-period");
    const rankingSize = document.getElementById("ranking-size");
    const playerNameInput = document.getElementById("player-name");
    
    async function loadRecords() {
        try {
            const params = new URLSearchParams({period: rankingPeriod.value, size: rankingSize.value});
            const response = await fetch("/api/records?" + params.toString());
            if (!response.ok) throw new Error("記録を読み込めません");
            const data = await response.json();
            renderBestList(data.bests || {});
            renderRanking(data.records || []);
            updateBestDisplay(data.bests || {});
        } catch (error) {
            document.getElementById("best-list").textContent = "記録を読み込めませんでした。";
            document.getElementById("ranking").textContent = "記録を読み込めませんでした。";
        }
    }

    function updateBestDisplay(bests = null) {
        if (bests === null) {
            // 記録は loadRecords() が取得し、表示を更新します。
            return;
        }
        const value = bests[String(getSize())];
        bestDisplay.textContent = value === undefined ? "--" : Number(value).toFixed(2);
        bestUnit.textContent = value === undefined ? "" : "秒";
    }

    function renderBestList(bests) {
        const container = document.getElementById("best-list");
        const sizes = [3, 4, 5];
        container.innerHTML = "";
        let hasRecord = false;

        sizes.forEach(size => {
            const value = bests[String(size)];
            const line = document.createElement("div");
            line.className = "record-line";

            const label = document.createElement("span");
            label.textContent = `${size === 3 ? "🌱" : size === 4 ? "⭐" : "🔥"} ${getDifficultyLabel(size)}`;

            const time = document.createElement("span");
            time.className = "record-time";
            time.textContent = value === undefined ? "--" : `${Number(value).toFixed(2)} 秒`;

            if (value !== undefined) hasRecord = true;
            line.append(label, time);
            container.appendChild(line);
        });

        if (!hasRecord) {
            const note = document.createElement("p");
            note.className = "empty";
            note.textContent = "まだ記録がありません。まずは1回クリアしよう！";
            container.appendChild(note);
        }
    }

    function renderRanking(records) {
        const container = document.getElementById("ranking");
        container.innerHTML = "";

        if (!records.length) {
            container.className = "empty";
            container.textContent = "まだランキング記録がありません。";
            return;
        }

        container.className = "";
        records.slice(0, 10).forEach((record, index) => {
            const line = document.createElement("div");
            line.className = "record-line";

            const label = document.createElement("span");
            const medal = index === 0 ? "🥇" : index === 1 ? "🥈" : index === 2 ? "🥉" : `${index + 1}.`;
            label.textContent = `${medal} ${record.player || "プレイヤー"}（${record.size}×${record.size}）`;

            const time = document.createElement("span");
            time.className = "record-time";
            time.textContent = `${Number(record.time).toFixed(2)} 秒`;

            line.append(label, time);
            container.appendChild(line);
        });
    }

    startButton.addEventListener("click", startCountdown);
    resetButton.addEventListener("click", resetGame);
    shareButton.addEventListener("click", () => {
        if (!lastResult) return;
        const name = lastResult.player || "プレイヤー";
        const text = `数字タッチ！ ${name} が ${lastResult.size}×${lastResult.size} を ${lastResult.time.toFixed(2)} 秒でクリア！
あなたも挑戦してみてね！`;
        const url = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(location.href)}`;
        window.open(url, "_blank", "noopener,noreferrer");
    });
    rankingPeriod.addEventListener("change", loadRecords);
    rankingSize.addEventListener("change", loadRecords);
    playerNameInput.value = localStorage.getItem("numberTouchPlayerName") || "";
    playerNameInput.addEventListener("change", () => localStorage.setItem("numberTouchPlayerName", playerNameInput.value.trim().slice(0, 16)));
    difficulty.addEventListener("change", resetGame);
    penaltySelect.addEventListener("change", () => {
        if (gameState === "ready") {
            penaltySeconds = Number(penaltySelect.value);
        }
    });

    resetGame();
</script>
</body>
</html>
"""


def get_connection():
    """DATABASE_URL があれば PostgreSQL、なければローカルの SQLite を使う。"""
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if database_url:
        import psycopg2
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        return psycopg2.connect(database_url), True
    import sqlite3
    conn = sqlite3.connect(DATA_FILE, timeout=10)
    return conn, False


def init_db():
    conn, is_postgres = get_connection()
    try:
        cur = conn.cursor()
        if is_postgres:
            cur.execute("""CREATE TABLE IF NOT EXISTS game_records (
                id BIGSERIAL PRIMARY KEY,
                player VARCHAR(16) NOT NULL,
                size INTEGER NOT NULL,
                time DOUBLE PRECISION NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )""")
        else:
            cur.execute("""CREATE TABLE IF NOT EXISTS game_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player TEXT NOT NULL,
                size INTEGER NOT NULL,
                time REAL NOT NULL,
                created_at TEXT NOT NULL
            )""")
        conn.commit()
    finally:
        conn.close()


def fetch_records():
    conn, is_postgres = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT player, size, time, created_at FROM game_records")
        rows = cur.fetchall()
        records = []
        for player, size, game_time, created_at in rows:
            if hasattr(created_at, "isoformat"):
                created_at = created_at.isoformat()
            records.append({"player": player, "size": int(size), "time": float(game_time), "created_at": str(created_at)})
        return records
    finally:
        conn.close()


def insert_record(player, size, game_time):
    conn, is_postgres = get_connection()
    try:
        cur = conn.cursor()
        created_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        if is_postgres:
            cur.execute("INSERT INTO game_records (player, size, time) VALUES (%s, %s, %s)", (player, size, game_time))
        else:
            cur.execute("INSERT INTO game_records (player, size, time, created_at) VALUES (?, ?, ?, ?)", (player, size, game_time, created_at))
        conn.commit()
    finally:
        conn.close()


@app.route("/")
def home():
    return render_template_string(HTML)


def _safe_jst_date(record):
    try:
        date_text = record["created_at"].replace("Z", "+00:00")
        dt = datetime.fromisoformat(date_text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(ZoneInfo("Asia/Tokyo")).date()
    except (ValueError, TypeError):
        return datetime.min.date()


@app.route("/api/records", methods=["GET"])
def get_records():
    period = request.args.get("period", "all")
    size_filter = request.args.get("size", "5")
    now_jst = datetime.now(ZoneInfo("Asia/Tokyo"))
    records = fetch_records()
    if size_filter in ("3", "4", "5"):
        records = [r for r in records if r["size"] == int(size_filter)]
    if period == "day":
        records = [r for r in records if _safe_jst_date(r) == now_jst.date()]
    elif period == "week":
        cutoff = now_jst.date().toordinal() - now_jst.weekday()
        records = [r for r in records if _safe_jst_date(r).toordinal() >= cutoff]

    records.sort(key=lambda r: r["time"])
    all_records = fetch_records()
    bests = {}
    for record in all_records:
        key = str(record["size"])
        if key not in bests or record["time"] < bests[key]:
            bests[key] = record["time"]
    return jsonify({"records": records[:10], "bests": bests})


@app.route("/api/records", methods=["POST"])
def save_record():
    data = request.get_json(silent=True) or {}
    player = " ".join(str(data.get("player", "")).split()).strip()[:16]
    try:
        size = int(data.get("size"))
        game_time = float(data.get("time"))
    except (TypeError, ValueError):
        return jsonify({"error": "記録の形式が正しくありません。"}), 400
    if not player:
        return jsonify({"error": "ニックネームを入力してください。"}), 400
    if size not in (3, 4, 5):
        return jsonify({"error": "難易度が正しくありません。"}), 400
    # 速すぎる記録や異常値を簡易的に拒否（本格的な不正対策ではありません）
    minimum_time = {3: 1.0, 4: 2.0, 5: 3.0}[size]
    if game_time < minimum_time or game_time > 3600:
        return jsonify({"error": "タイムが不正です。もう一度プレイしてください。"}), 400
    try:
        previous = [r["time"] for r in fetch_records() if r["size"] == size and r["player"].casefold() == player.casefold()]
        is_best = not previous or game_time < min(previous)
        insert_record(player, size, round(game_time, 2))
    except Exception:
        app.logger.exception("Could not save game record")
        return jsonify({"error": "ランキングを保存できませんでした。時間をおいて再度お試しください。"}), 500
    return jsonify({"ok": True, "is_best": is_best})


init_db()

if __name__ == "__main__":
    # ローカル確認用。公開時はホスティングサービスの起動コマンドを使用します。
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)

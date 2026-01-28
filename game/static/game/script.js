// ===== グローバル変数 =====
let sessionId = null;
let pokemonList = [];
let currentAttempts = 0;
let maxAttempts = 8; // デフォルト値
let selectedIndex = -1;

// ===== DOM要素 =====
const elements = {
    // 画面
    startScreen: document.getElementById('startScreen'),
    gameScreen: document.getElementById('gameScreen'),
    resultScreen: document.getElementById('resultScreen'),
    loading: document.getElementById('loading'),

    // ボタン
    startBtn: document.getElementById('startBtn'),
    guessBtn: document.getElementById('guessBtn'),
    playAgainBtn: document.getElementById('playAgainBtn'),

    // 入力
    pokemonInput: document.getElementById('pokemonInput'),
    autocompleteList: document.getElementById('autocompleteList'),

    // 表示
    attemptsValue: document.getElementById('attemptsValue'),
    resultsArea: document.getElementById('resultsArea'),

    // 結果画面
    resultIcon: document.getElementById('resultIcon'),
    resultTitle: document.getElementById('resultTitle'),
    resultMessage: document.getElementById('resultMessage'),
    answerValue: document.getElementById('answerValue'),

    // 統計
    totalGames: document.getElementById('totalGames'),
    clearRate: document.getElementById('clearRate'),
    avgAttempts: document.getElementById('avgAttempts'),
    bestAttempts: document.getElementById('bestAttempts'),

    // 設定
    settingsBtn: document.getElementById('settingsBtn'),
    settingsModal: document.getElementById('settingsModal'),
    settingsOverlay: document.getElementById('settingsOverlay'),
    settingsClose: document.getElementById('settingsClose'),
    settingsCancel: document.getElementById('settingsCancel'),
    settingsSave: document.getElementById('settingsSave'),
    maxAttemptsSlider: document.getElementById('maxAttemptsSlider'),
    maxAttemptsValue: document.getElementById('maxAttemptsValue'),
    startMaxAttempts: document.getElementById('startMaxAttempts'),
};

// ===== 初期化 =====
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    loadPokemonList();
    loadStats();
    loadSettings();
    initializeLoadingOverlay();
});

// ===== ロードオーバーレイ初期化 =====
function initializeLoadingOverlay() {
    const overlay = document.getElementById('loading-overlay');
    const loadingBar = document.getElementById('loading-bar');
    const loadingText = document.getElementById('loading-text');

    let progress = 0;
    const messages = [
        '読み込み中...',
        'ポケモンデータを取得中...',
        'ゲームを準備中...',
        '準備完了！'
    ];

    const interval = setInterval(() => {
        progress += Math.random() * 15 + 5;

        if (progress >= 100) {
            progress = 100;
            clearInterval(interval);

            loadingText.textContent = messages[3];
            loadingBar.style.width = '100%';

            setTimeout(() => {
                overlay.classList.add('fade-out');
                setTimeout(() => {
                    overlay.style.display = 'none';
                }, 500);
            }, 300);
        } else {
            const messageIndex = Math.min(Math.floor(progress / 33), 2);
            loadingText.textContent = messages[messageIndex];
            loadingBar.style.width = progress + '%';
        }
    }, 150);
}

// ===== イベントリスナー設定 =====
function initializeEventListeners() {
    elements.startBtn.addEventListener('click', startGame);
    elements.guessBtn.addEventListener('click', guessPokemon);
    elements.playAgainBtn.addEventListener('click', resetGame);

    elements.pokemonInput.addEventListener('input', handleInput);
    elements.pokemonInput.addEventListener('keydown', handleKeyDown);

    // 設定モーダル
    elements.settingsBtn.addEventListener('click', openSettings);
    elements.settingsClose.addEventListener('click', closeSettings);
    elements.settingsCancel.addEventListener('click', closeSettings);
    elements.settingsSave.addEventListener('click', saveSettings);
    elements.settingsOverlay.addEventListener('click', closeSettings);
    elements.maxAttemptsSlider.addEventListener('input', updateSliderValue);

    // オートコンプリート外クリックで閉じる
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.input-wrapper')) {
            hideAutocomplete();
        }
    });
}

// ===== ポケモンリスト読み込み =====
async function loadPokemonList() {
    try {
        const response = await fetch('/api/autocomplete/');
        const data = await response.json();
        pokemonList = data.pokemon;
    } catch (error) {
        console.error('ポケモンリストの読み込みに失敗:', error);
    }
}

// ===== 統計情報読み込み =====
async function loadStats() {
    try {
        const response = await fetch('/api/stats/');
        const data = await response.json();

        elements.totalGames.textContent = data.total_games;
        elements.clearRate.textContent = `${Math.round(data.clear_rate)}%`;
        elements.avgAttempts.textContent = data.average_attempts > 0
            ? data.average_attempts.toFixed(1)
            : '0';
        elements.bestAttempts.textContent = data.best_attempts > 0
            ? data.best_attempts
            : '-';
    } catch (error) {
        console.error('統計情報の読み込みに失敗:', error);
    }
}

// ===== ゲーム開始 =====
async function startGame() {
    showLoading();

    try {
        const response = await fetch('/api/start-game/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        const data = await response.json();

        if (data.session_id) {
            sessionId = data.session_id;
            currentAttempts = 0;

            // 結果エリアをクリア
            clearResults();

            // 画面切り替え
            hideLoading();
            hideScreen(elements.startScreen);
            showScreen(elements.gameScreen);

            // 入力フォーカス
            elements.pokemonInput.focus();

            updateAttemptsDisplay();
        } else {
            throw new Error('セッションIDが取得できませんでした');
        }
    } catch (error) {
        console.error('ゲーム開始エラー:', error);
        alert('ゲームの開始に失敗しました。もう一度お試しください。');
        hideLoading();
    }
}

// ===== ポケモン推測 =====
async function guessPokemon() {
    const pokemonName = elements.pokemonInput.value.trim();

    if (!pokemonName) {
        alert('ポケモンの名前を入力してください');
        return;
    }

    if (!pokemonList.includes(pokemonName)) {
        alert('正しいポケモンの名前を入力してください');
        return;
    }

    showLoading();

    try {
        const response = await fetch('/api/guess/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: sessionId,
                pokemon_name: pokemonName,
            }),
        });

        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        // 結果を表示
        addResultRow(data);

        // 試行回数更新
        currentAttempts = data.attempts;
        updateAttemptsDisplay();

        // 入力クリア
        elements.pokemonInput.value = '';
        hideAutocomplete();

        // ゲーム終了判定
        if (data.game_status === 'cleared') {
            setTimeout(() => showResult(true, data.answer, data.attempts), 500);
        } else if (data.game_status === 'failed') {
            setTimeout(() => showResult(false, data.answer, data.attempts), 500);
        } else {
            elements.pokemonInput.focus();
        }

        hideLoading();
    } catch (error) {
        console.error('推測エラー:', error);
        alert('推測に失敗しました: ' + error.message);
        hideLoading();
    }
}

// ===== 結果行追加 =====
function addResultRow(data) {
    const row = document.createElement('div');
    row.className = 'result-row';

    // 名前
    const nameCell = createCell(data.name, data.name_match ? 'match' : 'mismatch');

    // 図鑑番号
    const pokedexCell = createCell(data.pokedex_number, data.pokedex_match);

    // タイプ
    const typeCell = document.createElement('div');
    typeCell.className = `result-cell ${data.type_match}`;
    const typesDiv = document.createElement('div');
    typesDiv.className = 'cell-types';
    typesDiv.innerHTML = `
        <span>${data.type1}</span>
        ${data.type2 ? `<span>${data.type2}</span>` : ''}
    `;
    typeCell.appendChild(typesDiv);

    // 身長
    const heightCell = createCell(`${data.height}m`, data.height_match);

    // 体重
    const weightCell = createCell(`${data.weight}kg`, data.weight_match);

    // 世代
    const generationCell = createCell(`第${data.generation}世代`, data.generation_match);

    // 進化回数
    const evolutionCell = createCell(`${data.evolution_count}回`, data.evolution_match);

    row.appendChild(nameCell);
    row.appendChild(pokedexCell);
    row.appendChild(typeCell);
    row.appendChild(heightCell);
    row.appendChild(weightCell);
    row.appendChild(generationCell);
    row.appendChild(evolutionCell);

    // 結果エリアの先頭に追加（新しい結果が上に来る）
    const header = elements.resultsArea.querySelector('.results-header');
    if (header.nextSibling) {
        elements.resultsArea.insertBefore(row, header.nextSibling);
    } else {
        elements.resultsArea.appendChild(row);
    }
}

// ===== セル作成 =====
function createCell(value, matchType) {
    const cell = document.createElement('div');
    cell.className = `result-cell ${matchType}`;

    const valueSpan = document.createElement('span');
    valueSpan.className = 'cell-value';
    valueSpan.textContent = value;

    cell.appendChild(valueSpan);

    return cell;
}

// ===== 結果画面表示 =====
function showResult(success, answer, attempts) {
    if (success) {
        elements.resultIcon.textContent = '🎉';
        elements.resultTitle.textContent = 'クリア！';
        elements.resultTitle.className = 'result-title success';
        elements.resultMessage.textContent = `${attempts}回の試行で正解しました！`;
    } else {
        elements.resultIcon.textContent = '😢';
        elements.resultTitle.textContent = '失敗...';
        elements.resultTitle.className = 'result-title failure';
        elements.resultMessage.textContent = `${maxAttempts}回以内に当てられませんでした`;
    }

    elements.answerValue.textContent = answer;

    hideScreen(elements.gameScreen);
    showScreen(elements.resultScreen);

    // 統計情報を更新
    loadStats();
}

// ===== ゲームリセット =====
function resetGame() {
    hideScreen(elements.resultScreen);
    showScreen(elements.startScreen);
    sessionId = null;
    currentAttempts = 0;
}

// ===== 入力処理 =====
function handleInput(e) {
    const value = e.target.value.trim();

    if (value.length === 0) {
        hideAutocomplete();
        return;
    }

    const filtered = pokemonList.filter(name =>
        name.includes(value)
    ).slice(0, 10);

    if (filtered.length > 0) {
        showAutocomplete(filtered);
    } else {
        hideAutocomplete();
    }
}

// ===== キーボード操作 =====
function handleKeyDown(e) {
    const items = elements.autocompleteList.querySelectorAll('.autocomplete-item');

    if (e.key === 'ArrowDown') {
        e.preventDefault();
        selectedIndex = Math.min(selectedIndex + 1, items.length - 1);
        updateSelection(items);
    } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        selectedIndex = Math.max(selectedIndex - 1, -1);
        updateSelection(items);
    } else if (e.key === 'Enter') {
        e.preventDefault();
        if (selectedIndex >= 0 && items[selectedIndex]) {
            selectPokemon(items[selectedIndex].textContent);
        } else {
            guessPokemon();
        }
    } else if (e.key === 'Escape') {
        hideAutocomplete();
    }
}

// ===== オートコンプリート表示 =====
function showAutocomplete(items) {
    elements.autocompleteList.innerHTML = '';
    selectedIndex = -1;

    items.forEach((name, index) => {
        const item = document.createElement('div');
        item.className = 'autocomplete-item';
        item.textContent = name;

        item.addEventListener('click', () => selectPokemon(name));
        item.addEventListener('mouseenter', () => {
            selectedIndex = index;
            updateSelection(elements.autocompleteList.querySelectorAll('.autocomplete-item'));
        });

        elements.autocompleteList.appendChild(item);
    });

    elements.autocompleteList.classList.add('active');
}

// ===== オートコンプリート非表示 =====
function hideAutocomplete() {
    elements.autocompleteList.classList.remove('active');
    selectedIndex = -1;
}

// ===== 選択更新 =====
function updateSelection(items) {
    items.forEach((item, index) => {
        if (index === selectedIndex) {
            item.classList.add('selected');
            item.scrollIntoView({ block: 'nearest' });
        } else {
            item.classList.remove('selected');
        }
    });
}

// ===== ポケモン選択 =====
function selectPokemon(name) {
    elements.pokemonInput.value = name;
    hideAutocomplete();
    elements.pokemonInput.focus();
}

// ===== 試行回数表示更新 =====
function updateAttemptsDisplay() {
    elements.attemptsValue.textContent = `${currentAttempts} / ${maxAttempts}`;
}

// ===== 結果クリア =====
function clearResults() {
    const rows = elements.resultsArea.querySelectorAll('.result-row');
    rows.forEach(row => row.remove());
}

// ===== 画面表示/非表示 =====
function showScreen(screen) {
    screen.classList.remove('hidden');
}

function hideScreen(screen) {
    screen.classList.add('hidden');
}

function showLoading() {
    elements.loading.classList.remove('hidden');
}

function hideLoading() {
    elements.loading.classList.add('hidden');
}

// ===== 設定読み込み =====
async function loadSettings() {
    try {
        const response = await fetch('/api/settings/');
        const data = await response.json();
        maxAttempts = data.max_attempts;
        elements.maxAttemptsSlider.value = maxAttempts;
        elements.maxAttemptsValue.textContent = maxAttempts;
        elements.startMaxAttempts.textContent = maxAttempts;
    } catch (error) {
        console.error('設定の読み込みに失敗:', error);
    }
}

// ===== 設定モーダルを開く =====
function openSettings() {
    elements.settingsModal.classList.remove('hidden');
}

// ===== 設定モーダルを閉じる =====
function closeSettings() {
    elements.settingsModal.classList.add('hidden');
}

// ===== スライダー値更新 =====
function updateSliderValue() {
    elements.maxAttemptsValue.textContent = elements.maxAttemptsSlider.value;
}

// ===== 設定保存 =====
async function saveSettings() {
    const newMaxAttempts = parseInt(elements.maxAttemptsSlider.value);

    try {
        const response = await fetch('/api/settings/update/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                max_attempts: newMaxAttempts,
            }),
        });

        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        maxAttempts = newMaxAttempts;
        elements.startMaxAttempts.textContent = maxAttempts;
        updateAttemptsDisplay();
        closeSettings();
        alert('設定を保存しました！');
    } catch (error) {
        console.error('設定の保存に失敗:', error);
        alert('設定の保存に失敗しました: ' + error.message);
    }
}

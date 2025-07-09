let config = {
    backend_capture_interval: 5,
    show_table_cards: true,
    show_positions: true,
    show_moves: true,
    show_solver_link: true
};
let socket = null;
let previousDetections = [];

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!');
    }).catch(err => {
        console.error('Failed to copy:', err);
        showToast('Failed to copy!');
    });
}

function showToast(message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => {
        toast.classList.remove('show');
    }, 2000);
}

function showUpdateIndicator() {
    const indicator = document.getElementById('updateIndicator');
    indicator.classList.add('show');
    setTimeout(() => {
        indicator.classList.remove('show');
    }, 1000);
}

function updateConnectionStatus(status, message) {
    const statusEl = document.getElementById('connectionStatus');
    statusEl.className = `connection-status ${status}`;
    statusEl.textContent = message;
}

function getSuitColor(card) {
    const suit = card.slice(-1);
    if (suit === '♥') return 'red';
    if (suit === '♦') return 'blue';
    if (suit === '♣') return 'green';
    return 'black';
}

function detectChanges(newDetections) {
    const newStr = JSON.stringify(newDetections);
    const prevStr = JSON.stringify(previousDetections);
    return newStr !== prevStr;
}

function createPlayerCardsSection(detection, isUpdate) {
    const cardsClass = isUpdate ? 'cards-block new-cards' : 'cards-block';

    if (detection.player_cards && detection.player_cards.length > 0) {
        const cardsHtml = detection.player_cards.map(card =>
            `<div class="card ${getSuitColor(card.display)}">${card.display}</div>`
        ).join('');

        return `<div class="${cardsClass}" onclick="copyToClipboard('${detection.player_cards_string}')">${cardsHtml}</div>`;
    }

    return '<div class="no-cards">No cards detected</div>';
}

function createTableCardsSection(detection, isUpdate) {
    if (!config.show_table_cards) {
        return '';
    }

    const cardsClass = isUpdate ? 'cards-block new-cards' : 'cards-block';
    const streetClass = detection.street && detection.street.startsWith('ERROR') ? 'street-indicator error' : 'street-indicator';
    const streetDisplay = detection.street ? `<span class="${streetClass}">${detection.street}</span>` : '';

    let cardsHtml = '';
    if (detection.table_cards && detection.table_cards.length > 0) {
        const cards = detection.table_cards.map(card =>
            `<div class="card ${getSuitColor(card.display)}">${card.display}</div>`
        ).join('');
        cardsHtml = `<div class="${cardsClass}" onclick="copyToClipboard('${detection.table_cards_string}')">${cards}</div>`;
    } else {
        cardsHtml = '<div class="no-cards">No cards detected</div>';
    }

    return `
        <div class="table-cards-column">
            <div class="cards-label">Table Cards: ${streetDisplay}</div>
            <div class="cards-container">${cardsHtml}</div>
        </div>
    `;
}

function createPositionsSection(detection, isUpdate) {
    if (!config.show_positions) {
        return '';
    }

    const positionsClass = isUpdate ? 'positions-block new-positions' : 'positions-block';

    let positionsHtml = '';
    if (detection.positions && detection.positions.length > 0) {
        const positions = detection.positions.map(position =>
            `<div class="position">${position.player} ${position.name}</div>`
        ).join('');
        positionsHtml = `<div class="${positionsClass}">${positions}</div>`;
    } else {
        positionsHtml = '<div class="no-positions">No position detected</div>';
    }

    return `
        <div class="positions-column">
            <div class="cards-label">Positions:</div>
            <div class="positions-container">
                ${positionsHtml}
            </div>
        </div>
    `;
}

function createMovesSection(detection, isUpdate) {
    if (!config.show_moves) {
        return '';
    }

    if (!detection.moves || detection.moves.length === 0) {
        return `
            <div class="cards-section">
                <div class="cards-label">Moves History:</div>
                <div class="moves-by-street">
                    <div class="no-moves">No moves detected</div>
                </div>
            </div>
        `;
    }

    const movesClass = isUpdate ? 'street-moves-block new-moves' : 'street-moves-block';

    const movesHtml = detection.moves.map(streetData => {
        const moves = streetData.moves.map(move => {
            let moveText = `${move.player_label}: ${move.action}`;
            if (move.amount > 0) {
                moveText += ` $${move.amount}`;
            }
            return `<div class="move">${moveText}</div>`;
        }).join('');

        return `
            <div class="${movesClass}">
                <div class="street-moves-header">${streetData.street}</div>
                <div class="street-moves-list">${moves}</div>
            </div>
        `;
    }).join('');

    return `
        <div class="cards-section">
            <div class="cards-label">Moves History:</div>
            <div class="moves-by-street">
                ${movesHtml}
            </div>
        </div>
    `;
}

function createSolverLinkSection(detection, isUpdate) {
    if (!config.show_solver_link || !detection.solver_link) {
        return '';
    }

    const linkClass = isUpdate ? 'solver-link-block new-solver-link' : 'solver-link-block';

    return `
        <div class="cards-section">
            <div class="cards-label">Solver Analysis !!!BETA!!!:</div>
            <div class="${linkClass}">
                <a href="${detection.solver_link}" target="_blank" class="solver-link">
                    Open in FlopHero 🔗
                </a>
            </div>
        </div>
    `;
}

function createTableContainer(detection, isUpdate) {
    const tableClass = isUpdate ? 'table-container updated' : 'table-container';

    const tableCardsSection = createTableCardsSection(detection, isUpdate);
    const positionsSection = createPositionsSection(detection, isUpdate);
    const movesSection = createMovesSection(detection, isUpdate);
    const solverLinkSection = createSolverLinkSection(detection, isUpdate);

    // Build main cards section conditionally
    let mainCardsContent = `
        <div class="player-cards-column">
            <div class="cards-label">Player Cards:</div>
            <div class="player-section">
                ${createPlayerCardsSection(detection, isUpdate)}
            </div>
        </div>
    `;

    if (tableCardsSection) {
        mainCardsContent += tableCardsSection;
    }

    if (positionsSection) {
        mainCardsContent += positionsSection;
    }

    return `
        <div class="${tableClass}">
            <div class="table-name">${detection.window_name}</div>
            <div class="main-cards-section">
                ${mainCardsContent}
            </div>
            ${movesSection}
            ${solverLinkSection}
        </div>
    `;
}

function renderCards(detections, isUpdate = false) {
    const content = document.getElementById('content');

    if (!detections || detections.length === 0) {
        content.innerHTML = '<div class="error">No tables detected</div>';
        return;
    }

    const html = detections.map(detection =>
        createTableContainer(detection, isUpdate)
    ).join('');

    content.innerHTML = html;

    if (isUpdate) {
        setTimeout(() => {
            document.querySelectorAll('.updated').forEach(el => {
                el.classList.remove('updated');
            });
            document.querySelectorAll('.new-positions').forEach(el => {
                el.classList.remove('new-positions');
            });
            document.querySelectorAll('.new-moves').forEach(el => {
                el.classList.remove('new-moves');
            });
            document.querySelectorAll('.new-cards').forEach(el => {
                el.classList.remove('new-cards');
            });
            document.querySelectorAll('.new-solver-link').forEach(el => {
                el.classList.remove('new-solver-link');
            });
        }, 2000);
    }
}

function updateStatus(lastUpdate) {
    const status = document.getElementById('status');
    if (lastUpdate) {
        const date = new Date(lastUpdate);
        status.textContent = `Last update: ${date.toLocaleTimeString()} (Real-time)`;
    }
}

function updateTimerDisplay() {
    document.getElementById('backendInfo').textContent = `every ${config.backend_capture_interval}`;
}

function initializeSocketIO() {
    if (socket) {
        socket.disconnect();
    }

    updateConnectionStatus('connecting', '🔗 Connecting...');

    // Initialize Socket.IO
    socket = io();

    socket.on('connect', function() {
        console.log('SocketIO connected');
        updateConnectionStatus('connected', '🟢 Connected');
    });

    socket.on('disconnect', function() {
        console.log('SocketIO disconnected');
        updateConnectionStatus('disconnected', '🔴 Disconnected');

        // Attempt to reconnect after 3 seconds
        setTimeout(() => {
            if (socket && !socket.connected) {
                console.log('Attempting to reconnect...');
                socket.connect();
            }
        }, 3000);
    });

    socket.on('detection_update', function(data) {
        console.log('Received detection update:', data);

        const hasChanges = detectChanges(data.detections);
        if (hasChanges) {
            showUpdateIndicator();
        }

        updateStatus(data.last_update);
        renderCards(data.detections, hasChanges);
        previousDetections = data.detections;
    });

    socket.on('connect_error', function(error) {
        console.error('SocketIO connection error:', error);
        updateConnectionStatus('disconnected', '🔴 Connection Error');
    });
}

async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        const data = await response.json();
        config = data;
        updateTimerDisplay();
        console.log('Loaded config:', config);
    } catch (error) {
        console.error('Error loading config:', error);
    }
}

async function initialize() {
    await loadConfig();

    if (typeof io !== "undefined") {
        console.log('Initializing with SocketIO...');
        initializeSocketIO();
    } else {
        console.error('SocketIO not loaded');
        document.getElementById('content').innerHTML = '<div class="error">SocketIO library not loaded</div>';
        updateConnectionStatus('disconnected', '🔴 Not Supported');
    }
}

// Handle page visibility changes
document.addEventListener('visibilitychange', function() {
    if (!document.hidden && socket && !socket.connected) {
        console.log('Page visible again, reconnecting...');
        socket.connect();
    }
});

// Handle page restoration from cache
window.addEventListener('pageshow', function(event) {
    if (event.persisted && socket && !socket.connected) {
        console.log('Page restored from cache, reconnecting...');
        socket.connect();
    }
});

initialize();
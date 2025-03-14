// Initialize canvas and game state
const canvas = document.getElementById('slotCanvas');
const ctx = canvas.getContext('2d');
const REEL_COUNT = 3;
const SYMBOL_COUNT = 8;
const SYMBOL_SIZE = 100;
const SPIN_TIME = 2000;
const SYMBOLS = [
    '🍒', '💎', '7️⃣', '🎰', '⭐', '🎲', '🎮', '🎯'
];

let spinning = false;
let reels = Array(REEL_COUNT).fill().map(() => ({
    currentPos: 0,
    finalSymbol: 0,
    spinSpeed: 0
}));

// Draw functions
function drawSymbol(symbol, x, y) {
    ctx.font = '80px Arial';
    ctx.fillStyle = '#fff';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(symbol, x + SYMBOL_SIZE/2, y + SYMBOL_SIZE/2);
}

function drawReel(reelIndex, offset) {
    const x = reelIndex * SYMBOL_SIZE;
    for(let i = -1; i <= 1; i++) {
        const symbolIndex = (reels[reelIndex].currentPos + i + SYMBOL_COUNT) % SYMBOL_COUNT;
        drawSymbol(SYMBOLS[symbolIndex], x, (i + 1) * SYMBOL_SIZE + offset);
    }
}

function draw() {
    ctx.fillStyle = '#2C2F33';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    reels.forEach((reel, i) => drawReel(i, 0));
    
    // Draw frame
    ctx.strokeStyle = '#FFD700';
    ctx.lineWidth = 3;
    ctx.strokeRect(0, SYMBOL_SIZE, canvas.width, SYMBOL_SIZE);
}

// Spin animation
function animate(currentTime) {
    if(!spinning) return;
    
    let allStopped = true;
    reels.forEach((reel, i) => {
        reel.currentPos = (reel.currentPos + reel.spinSpeed) % SYMBOL_COUNT;
        if(reel.spinSpeed > 0) {
            reel.spinSpeed -= 0.01;
            if(reel.spinSpeed <= 0) {
                reel.spinSpeed = 0;
                reel.currentPos = reel.finalSymbol;
                if(i === REEL_COUNT - 1) {
                    checkWin();
                }
            } else {
                allStopped = false;
            }
        }
    });
    
    draw();
    if(!allStopped) {
        requestAnimationFrame(animate);
    } else {
        spinning = false;
    }
}

// Game logic
function spin() {
    if(spinning) return;
    
    const betAmount = parseFloat(document.getElementById('betAmount').value);
    const useBonus = document.getElementById('useBonus').checked;
    
    fetch('/api/spin', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            bet_amount: betAmount,
            game_id: GAME_ID,
            use_bonus: useBonus
        })
    })
    .then(response => response.json())
    .then(data => {
        if(data.error) {
            showMessage(data.error, 'error');
            return;
        }
        
        spinning = true;
        playSpinSound();
        
        reels.forEach((reel, i) => {
            reel.spinSpeed = 0.5 + i * 0.1;
            reel.finalSymbol = data.result.symbols[i];
        });
        
        requestAnimationFrame(animate);
        
        // Update balances
        document.getElementById('balance').textContent = data.regular_balance.toFixed(2);
        document.getElementById('bonusBalance').textContent = data.bonus_balance.toFixed(2);
        
        if(data.win_amount > 0) {
            setTimeout(() => {
                showMessage(`Won $${data.win_amount.toFixed(2)}!`, 'success');
                playWinSound();
            }, SPIN_TIME);
        }
    })
    .catch(err => {
        showMessage('Error connecting to server', 'error');
    });
}

function showMessage(msg, type) {
    const msgEl = document.getElementById('message');
    msgEl.textContent = msg;
    msgEl.className = `alert alert-${type === 'error' ? 'danger' : 'success'}`;
    msgEl.style.display = 'block';
    setTimeout(() => msgEl.style.display = 'none', 3000);
}

// Initialize game
canvas.width = SYMBOL_SIZE * REEL_COUNT;
canvas.height = SYMBOL_SIZE * 3;
draw();

document.getElementById('spinButton').addEventListener('click', spin);

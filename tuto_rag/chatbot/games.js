// ===== Mini Games for Loading Time =====

const GAMES = {
    // List of available games
    list: ['bubblePop', 'colorClick', 'emojiCatch', 'clickCounter', 'memoryFlash'],

    currentGame: null,
    score: 0,
    gameInterval: null,

    // Start a random game
    start(container) {
        this.score = 0;
        const randomGame = this.list[Math.floor(Math.random() * this.list.length)];
        this.currentGame = randomGame;

        container.innerHTML = '';
        container.style.position = 'relative';

        switch (randomGame) {
            case 'bubblePop':
                this.bubblePop(container);
                break;
            case 'colorClick':
                this.colorClick(container);
                break;
            case 'emojiCatch':
                this.emojiCatch(container);
                break;
            case 'clickCounter':
                this.clickCounter(container);
                break;
            case 'memoryFlash':
                this.memoryFlash(container);
                break;
        }
    },

    // Stop current game
    stop() {
        if (this.gameInterval) {
            clearInterval(this.gameInterval);
            this.gameInterval = null;
        }
        this.currentGame = null;
    },

    // ===== BUBBLE POP - Click bubbles to pop them =====
    bubblePop(container) {
        const gameArea = document.createElement('div');
        gameArea.className = 'game-area';
        gameArea.innerHTML = `
            <div class="game-title">🫧 Pop les bulles!</div>
            <div class="game-score">Score: <span id="gameScore">0</span></div>
            <div class="bubble-area" id="bubbleArea"></div>
        `;
        container.appendChild(gameArea);

        const bubbleArea = document.getElementById('bubbleArea');
        const scoreEl = document.getElementById('gameScore');

        const createBubble = () => {
            const bubble = document.createElement('div');
            bubble.className = 'bubble';
            bubble.style.left = Math.random() * 80 + '%';
            bubble.style.animationDuration = (Math.random() * 2 + 1) + 's';

            const colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeaa7', '#dfe6e9', '#a29bfe', '#fd79a8'];
            bubble.style.background = colors[Math.floor(Math.random() * colors.length)];
            bubble.style.width = bubble.style.height = (Math.random() * 30 + 20) + 'px';

            bubble.addEventListener('click', () => {
                this.score += 10;
                scoreEl.textContent = this.score;
                bubble.style.transform = 'scale(1.5)';
                bubble.style.opacity = '0';
                setTimeout(() => bubble.remove(), 200);
                this.createParticles(bubble.offsetLeft, bubble.offsetTop, container);
            });

            bubbleArea.appendChild(bubble);

            setTimeout(() => {
                if (bubble.parentNode) bubble.remove();
            }, 3000);
        };

        // Spawn bubbles
        this.gameInterval = setInterval(createBubble, 300);
        createBubble();
    },

    // ===== COLOR CLICK - Click the matching color =====
    colorClick(container) {
        const colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#ffeaa7', '#a29bfe', '#fd79a8'];
        let targetColor = colors[Math.floor(Math.random() * colors.length)];

        const gameArea = document.createElement('div');
        gameArea.className = 'game-area';
        gameArea.innerHTML = `
            <div class="game-title">🎨 Clique la bonne couleur!</div>
            <div class="game-score">Score: <span id="gameScore">0</span></div>
            <div class="target-color" id="targetColor" style="background: ${targetColor}"></div>
            <div class="color-grid" id="colorGrid"></div>
        `;
        container.appendChild(gameArea);

        const colorGrid = document.getElementById('colorGrid');
        const scoreEl = document.getElementById('gameScore');
        const targetEl = document.getElementById('targetColor');

        const renderColors = () => {
            colorGrid.innerHTML = '';
            const shuffled = [...colors].sort(() => Math.random() - 0.5);

            shuffled.forEach(color => {
                const btn = document.createElement('div');
                btn.className = 'color-btn';
                btn.style.background = color;
                btn.addEventListener('click', () => {
                    if (color === targetColor) {
                        this.score += 25;
                        scoreEl.textContent = this.score;
                        targetColor = colors[Math.floor(Math.random() * colors.length)];
                        targetEl.style.background = targetColor;
                        this.flashSuccess(container);
                        renderColors();
                    } else {
                        btn.classList.add('wrong');
                        setTimeout(() => btn.classList.remove('wrong'), 300);
                    }
                });
                colorGrid.appendChild(btn);
            });
        };

        renderColors();
    },

    // ===== EMOJI CATCH - Click falling emojis =====
    emojiCatch(container) {
        const emojis = ['🌟', '💎', '🔥', '⚡', '🎯', '💰', '🍕', '🎮', '🚀', '🎪', '🦄', '🍩', '💜', '🎁', '🌈', '👾', '🎵', '💫'];

        const gameArea = document.createElement('div');
        gameArea.className = 'game-area';
        gameArea.innerHTML = `
            <div class="game-title">✨ Attrape les emojis!</div>
            <div class="game-score">Score: <span id="gameScore">0</span></div>
            <div class="emoji-area" id="emojiArea"></div>
        `;
        container.appendChild(gameArea);

        const emojiArea = document.getElementById('emojiArea');
        const scoreEl = document.getElementById('gameScore');

        const createEmoji = () => {
            const emoji = document.createElement('div');
            emoji.className = 'falling-emoji';
            emoji.textContent = emojis[Math.floor(Math.random() * emojis.length)];
            emoji.style.left = Math.random() * 70 + 5 + '%';
            // Slower fall (3-5s) and random wiggle speed
            const fallDuration = Math.random() * 2 + 3;
            const wiggleDuration = Math.random() * 0.3 + 0.3;
            emoji.style.animationDuration = `${fallDuration}s, ${wiggleDuration}s`;

            emoji.addEventListener('click', () => {
                this.score += 15;
                scoreEl.textContent = this.score;
                emoji.style.animation = 'none';
                emoji.style.transform = 'scale(3) rotate(720deg)';
                emoji.style.opacity = '0';
                emoji.style.transition = 'all 0.4s ease-out';
                setTimeout(() => emoji.remove(), 400);
            });

            emojiArea.appendChild(emoji);

            setTimeout(() => {
                if (emoji.parentNode) emoji.remove();
            }, 6000);
        };

        // Spawn emojis faster
        this.gameInterval = setInterval(createEmoji, 300);
        createEmoji();
        createEmoji();
    },

    // ===== CLICK COUNTER - Click as fast as possible =====
    clickCounter(container) {
        const gameArea = document.createElement('div');
        gameArea.className = 'game-area';
        gameArea.innerHTML = `
            <div class="game-title">👆 Clique le plus vite possible!</div>
            <div class="game-score">Clics: <span id="gameScore">0</span></div>
            <div class="click-btn" id="clickBtn">
                <span class="click-emoji">🔴</span>
            </div>
        `;
        container.appendChild(gameArea);

        const clickBtn = document.getElementById('clickBtn');
        const scoreEl = document.getElementById('gameScore');

        clickBtn.addEventListener('click', (e) => {
            this.score++;
            scoreEl.textContent = this.score;

            // Visual feedback
            clickBtn.style.transform = 'scale(0.9)';
            setTimeout(() => clickBtn.style.transform = 'scale(1)', 100);

            // Create ripple
            const ripple = document.createElement('div');
            ripple.className = 'click-ripple';
            ripple.style.left = e.offsetX + 'px';
            ripple.style.top = e.offsetY + 'px';
            clickBtn.appendChild(ripple);
            setTimeout(() => ripple.remove(), 500);

            // Change color occasionally
            if (this.score % 10 === 0) {
                const colors = ['🔴', '🟠', '🟡', '🟢', '🔵', '🟣'];
                clickBtn.querySelector('.click-emoji').textContent = colors[Math.floor(Math.random() * colors.length)];
            }
        });
    },

    // ===== MEMORY FLASH - Remember the pattern =====
    memoryFlash(container) {
        const gameArea = document.createElement('div');
        gameArea.className = 'game-area';
        gameArea.innerHTML = `
            <div class="game-title">🧠 Mémorise le pattern!</div>
            <div class="game-score">Niveau: <span id="gameScore">1</span></div>
            <div class="memory-grid" id="memoryGrid"></div>
            <div class="memory-status" id="memoryStatus">Regarde bien...</div>
        `;
        container.appendChild(gameArea);

        const grid = document.getElementById('memoryGrid');
        const scoreEl = document.getElementById('gameScore');
        const statusEl = document.getElementById('memoryStatus');

        let pattern = [];
        let playerPattern = [];
        let level = 1;
        let canClick = false;

        // Create 9 cells
        for (let i = 0; i < 9; i++) {
            const cell = document.createElement('div');
            cell.className = 'memory-cell';
            cell.dataset.index = i;
            cell.addEventListener('click', () => {
                if (!canClick) return;

                cell.classList.add('active');
                setTimeout(() => cell.classList.remove('active'), 200);

                playerPattern.push(i);

                if (playerPattern[playerPattern.length - 1] !== pattern[playerPattern.length - 1]) {
                    statusEl.textContent = '❌ Raté! On recommence...';
                    level = 1;
                    this.score = level;
                    scoreEl.textContent = level;
                    setTimeout(() => startRound(), 1000);
                } else if (playerPattern.length === pattern.length) {
                    statusEl.textContent = '✅ Bravo! Niveau suivant...';
                    level++;
                    this.score = level;
                    scoreEl.textContent = level;
                    setTimeout(() => startRound(), 1000);
                }
            });
            grid.appendChild(cell);
        }

        const startRound = () => {
            canClick = false;
            playerPattern = [];
            pattern = [];
            statusEl.textContent = 'Regarde bien...';

            // Generate pattern
            for (let i = 0; i < level; i++) {
                pattern.push(Math.floor(Math.random() * 9));
            }

            // Show pattern
            let i = 0;
            const showNext = () => {
                if (i >= pattern.length) {
                    canClick = true;
                    statusEl.textContent = 'À ton tour!';
                    return;
                }

                const cell = grid.children[pattern[i]];
                cell.classList.add('active');
                setTimeout(() => {
                    cell.classList.remove('active');
                    i++;
                    setTimeout(showNext, 300);
                }, 500);
            };

            setTimeout(showNext, 500);
        };

        startRound();
    },

    // ===== Helper: Create particles =====
    createParticles(x, y, container) {
        for (let i = 0; i < 8; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.style.left = x + 'px';
            particle.style.top = y + 'px';
            particle.style.setProperty('--tx', (Math.random() - 0.5) * 100 + 'px');
            particle.style.setProperty('--ty', (Math.random() - 0.5) * 100 + 'px');
            container.appendChild(particle);
            setTimeout(() => particle.remove(), 500);
        }
    },

    // ===== Helper: Flash success =====
    flashSuccess(container) {
        container.style.boxShadow = '0 0 30px #4ecdc4';
        setTimeout(() => container.style.boxShadow = '', 200);
    }
};

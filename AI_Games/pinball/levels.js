// 游戏常量（从主文件复制）
const BRICK_COLUMNS = 10;
const BRICK_ROWS = 5;
const BRICK_WIDTH = 75;
const BRICK_HEIGHT = 30;
const BRICK_PADDING = 5;

// 关卡数据定义
const LEVELS = {
    1: {
        name: "基础关卡",
        bricks: createStandardLayout(),
        description: "标准砖块排列"
    },
    2: {
        name: "金字塔",
        bricks: createPyramidLayout(),
        description: "金字塔形状的砖块排列"
    },
    3: {
        name: "十字架",
        bricks: createCrossLayout(),
        description: "十字架形状的砖块排列"
    },
    4: {
        name: "边框",
        bricks: createBorderLayout(),
        description: "只有边框的砖块排列"
    },
    5: {
        name: "随机迷宫",
        bricks: createMazeLayout(),
        description: "随机生成的迷宫样式"
    }
};

// 标准布局 - 全屏砖块
function createStandardLayout() {
    const bricks = [];
    const colors = ['#FFF5BA', '#B5EAD7', '#FFD1DC', '#C9C9FF', '#E6E6FA'];
    
    for (let c = 0; c < BRICK_COLUMNS; c++) {
        bricks[c] = [];
        for (let r = 0; r < BRICK_ROWS; r++) {
            const brickX = c * (BRICK_WIDTH + BRICK_PADDING);
            const brickY = r * (BRICK_HEIGHT + BRICK_PADDING) + 60;
            
            let type = 'normal';
            let hits = 1;
            if (Math.random() < 0.3) {
                type = 'strong';
                hits = 2;
            }
            
            bricks[c][r] = {
                x: brickX,
                y: brickY,
                status: 1,
                hits: hits,
                type: type,
                color: colors[r % colors.length]
            };
        }
    }
    return bricks;
}

// 金字塔布局
function createPyramidLayout() {
    const bricks = [];
    const colors = ['#FFF5BA', '#B5EAD7', '#FFD1DC', '#C9C9FF', '#E6E6FA'];
    
    for (let c = 0; c < BRICK_COLUMNS; c++) {
        bricks[c] = [];
        for (let r = 0; r < BRICK_ROWS; r++) {
            const brickX = c * (BRICK_WIDTH + BRICK_PADDING);
            const brickY = r * (BRICK_HEIGHT + BRICK_PADDING) + 60;
            
            // 金字塔形状：中间砖块多，两边砖块少
            const center = Math.floor(BRICK_COLUMNS / 2);
            const distanceFromCenter = Math.abs(c - center);
            const maxRowForColumn = BRICK_ROWS - distanceFromCenter;
            
            if (r < maxRowForColumn) {
                let type = 'normal';
                let hits = 1;
                if (Math.random() < 0.3) {
                    type = 'strong';
                    hits = 2;
                }
                
                bricks[c][r] = {
                    x: brickX,
                    y: brickY,
                    status: 1,
                    hits: hits,
                    type: type,
                    color: colors[r % colors.length]
                };
            } else {
                bricks[c][r] = { status: 0 }; // 空砖块
            }
        }
    }
    return bricks;
}

// 十字架布局
function createCrossLayout() {
    const bricks = [];
    const colors = ['#FFF5BA', '#B5EAD7', '#FFD1DC', '#C9C9FF', '#E6E6FA'];
    
    for (let c = 0; c < BRICK_COLUMNS; c++) {
        bricks[c] = [];
        for (let r = 0; r < BRICK_ROWS; r++) {
            const brickX = c * (BRICK_WIDTH + BRICK_PADDING);
            const brickY = r * (BRICK_HEIGHT + BRICK_PADDING) + 60;
            
            // 十字架形状：中间行和中间列有砖块
            const centerCol = Math.floor(BRICK_COLUMNS / 2);
            const centerRow = Math.floor(BRICK_ROWS / 2);
            
            if (c === centerCol || r === centerRow) {
                let type = 'normal';
                let hits = 1;
                if (Math.random() < 0.4) {
                    type = 'strong';
                    hits = 2;
                }
                
                bricks[c][r] = {
                    x: brickX,
                    y: brickY,
                    status: 1,
                    hits: hits,
                    type: type,
                    color: colors[(c + r) % colors.length]
                };
            } else {
                bricks[c][r] = { status: 0 }; // 空砖块
            }
        }
    }
    return bricks;
}

// 边框布局
function createBorderLayout() {
    const bricks = [];
    const colors = ['#FFF5BA', '#B5EAD7', '#FFD1DC', '#C9C9FF', '#E6E6FA'];
    
    for (let c = 0; c < BRICK_COLUMNS; c++) {
        bricks[c] = [];
        for (let r = 0; r < BRICK_ROWS; r++) {
            const brickX = c * (BRICK_WIDTH + BRICK_PADDING);
            const brickY = r * (BRICK_HEIGHT + BRICK_PADDING) + 60;
            
            // 只有边框有砖块
            if (c === 0 || c === BRICK_COLUMNS - 1 || r === 0 || r === BRICK_ROWS - 1) {
                let type = 'normal';
                let hits = 1;
                if (Math.random() < 0.5) {
                    type = 'strong';
                    hits = 2;
                }
                
                bricks[c][r] = {
                    x: brickX,
                    y: brickY,
                    status: 1,
                    hits: hits,
                    type: type,
                    color: colors[(c + r) % colors.length]
                };
            } else {
                bricks[c][r] = { status: 0 }; // 空砖块
            }
        }
    }
    return bricks;
}

// 随机迷宫布局
function createMazeLayout() {
    const bricks = [];
    const colors = ['#FFF5BA', '#B5EAD7', '#FFD1DC', '#C9C9FF', '#E6E6FA'];
    
    for (let c = 0; c < BRICK_COLUMNS; c++) {
        bricks[c] = [];
        for (let r = 0; r < BRICK_ROWS; r++) {
            const brickX = c * (BRICK_WIDTH + BRICK_PADDING);
            const brickY = r * (BRICK_HEIGHT + BRICK_PADDING) + 60;
            
            // 随机生成迷宫样式，50%的概率生成砖块
            if (Math.random() < 0.5) {
                let type = 'normal';
                let hits = 1;
                if (Math.random() < 0.3) {
                    type = 'strong';
                    hits = 2;
                }
                
                bricks[c][r] = {
                    x: brickX,
                    y: brickY,
                    status: 1,
                    hits: hits,
                    type: type,
                    color: colors[(c + r) % colors.length]
                };
            } else {
                bricks[c][r] = { status: 0 }; // 空砖块
            }
        }
    }
    return bricks;
}
export type Locale = 'en' | 'zh';

const locales: Record<Locale, Record<string, string>> = {
  en: {
    // App / Header
    'app.title': "CYBER HOLD'EM",
    'app.subtitle': '1 HUMAN VS 5 AI BOTS',
    'app.start': '▶ START GAME',
    'app.nextHand': '▶ NEXT HAND',
    'app.newGame': '▶ NEW GAME',
    'app.continue': '▶ CONTINUE',
    'app.menu': '⏚ MENU',
    'header.blind': 'BLIND',
    'header.street': 'STREET',
    'header.pot': 'POT',
    'header.hand': 'HAND',
    'header.connected': '● CONNECTED',
    'header.disconnected': '● DISCONNECTED',

    // Actions
    'action.fold': 'FOLD',
    'action.check': 'CHECK',
    'action.call': 'CALL',
    'action.raise': 'RAISE',
    'action.allin': 'ALL IN',
    'action.askAi': '◈ ASK AI',
    'action.thinking': '◈ THINKING...',

    // Player status
    'status.fold': 'FOLD',
    'status.allin': 'ALL IN',
    'status.thinking': 'THINKING ▌',
    'status.bet': 'BET',
    'status.waiting': 'WAITING',

    // Bet controls
    'bet.halfPot': '½ POT',
    'bet.pot': 'POT',
    'bet.2xbb': '2×BB',
    'bet.step': 'STEP',
    'bet.odds': 'ODDS',

    // Dealer
    'dealer.label': '◈ DEALER',
    'dealer.dealing': '◈ DEALING...',
    'dealer.showdown': '◈ SHOWDOWN ◈',

    // Pot
    'pot.label': '◈ POT :',

    // Game over
    'gameover.title': 'GAME OVER',
    'gameover.eliminated': "You've been eliminated.",

    // HoleCards / HumanPanel
    'human.yourHand': 'YOUR HAND',
    'human.yourTurn': 'YOUR TURN',
    'human.you': 'YOU',
    'human.inPos': 'IN POS',
    'human.oop': 'OOP',

    // AI Coach
    'coach.title': '◈ AI COACH',
    'coach.thinking': '◈ AI THINKING...',
    'coach.recommend': 'Recommend:',
    'coach.empty': 'Click ◈ ASK AI to get advice',

    // Showdown
    'showdown.label': '◈ SHOWDOWN ◈',

    // Learning Mode
    'learn.toggle': 'LEARN',
    'learn.statsBtn': '📊 STATS',
    'learn.hintTitle': '◈ GTO HINT',
    'learn.reviewTitle': '◈ HAND REVIEW',
    'learn.netResult': 'NET:',
    'learn.grade.correct': 'CORRECT',
    'learn.grade.marginal': 'MARGINAL',
    'learn.grade.mistake': 'MISTAKE',
    'learn.caveat': 'Grades are a GTO-baseline approximation, not solver-exact. Use as a guide.',
    'learn.statsTitle': '◈ SESSION STATS',
    'learn.statsEmpty': 'Play a few hands to see your stats.',
    'learn.handsPlayed': 'HANDS',
    'learn.net': 'NET',
    'learn.leaksTitle': '◈ LEAK DETECTION',
    'learn.leaksEmpty': 'No leaks detected yet — keep playing.',

    // Setup lobby
    'setup.opponents': 'OPPONENTS',
    'setup.stack': 'STARTING STACK',
    'setup.speed': 'BLIND SPEED',
    'setup.speed.turbo': 'TURBO',
    'setup.speed.normal': 'NORMAL',
    'setup.speed.slow': 'SLOW',
    'setup.difficulty': 'DIFFICULTY',
    'setup.diff.easy': 'EASY',
    'setup.diff.normal': 'NORMAL',
    'setup.diff.hard': 'HARD',

    // Tournament
    'tour.level': 'LEVEL',
    'tour.blinds': 'BLINDS',
    'tour.nextLevel': 'NEXT LVL',
    'tour.remaining': 'LEFT',
    'tour.place': 'RANK',
    'tour.youWin': '🏆 YOU WIN!',
    'tour.over': 'TOURNAMENT OVER',
    'tour.yourFinish': 'YOU FINISHED',
    'tour.playAgain': '▶ PLAY AGAIN',
    'tour.blindsUp': 'BLINDS UP',

    // All-in
    'allin.title': 'ALL-IN EQUITY',

    // Career
    'career.button': '◈ CAREER',
    'career.title': '◈ CAREER',
    'career.empty': 'No tournaments yet. Play one to start your record.',
    'career.played': 'PLAYED',
    'career.wins': 'WINS',
    'career.winRate': 'WIN RATE',
    'career.best': 'BEST',
    'career.avg': 'AVG PLACE',
    'career.podiums': 'PODIUMS',
    'career.achievements': '◈ ACHIEVEMENTS',

    // Language
    'lang.select': 'SELECT LANGUAGE',
  },
  zh: {
    'app.title': '赛博德扑',
    'app.subtitle': '1 位玩家 VS 5 个 AI',
    'app.start': '▶ 开始游戏',
    'app.nextHand': '▶ 下一手',
    'app.newGame': '▶ 新游戏',
    'app.continue': '▶ 继续',
    'app.menu': '⏚ 菜单',
    'header.blind': '盲注',
    'header.street': '阶段',
    'header.pot': '底池',
    'header.hand': '手数',
    'header.connected': '● 已连接',
    'header.disconnected': '● 未连接',

    'action.fold': '弃牌',
    'action.check': '过牌',
    'action.call': '跟注',
    'action.raise': '加注',
    'action.allin': '全下',
    'action.askAi': '◈ AI分析',
    'action.thinking': '◈ 分析中...',

    'status.fold': '弃牌',
    'status.allin': '全下',
    'status.thinking': '思考中 ▌',
    'status.bet': '下注',
    'status.waiting': '等待中',

    'bet.halfPot': '½ 底池',
    'bet.pot': '底池',
    'bet.2xbb': '2×大盲',
    'bet.step': '步长',
    'bet.odds': '赔率',

    'dealer.label': '◈ 荷官',
    'dealer.dealing': '◈ 发牌中...',
    'dealer.showdown': '◈ 摊牌 ◈',

    'pot.label': '◈ 底池 :',

    'gameover.title': '游戏结束',
    'gameover.eliminated': '你的筹码已经输光了。',

    'human.yourHand': '你的手牌',
    'human.yourTurn': '你的回合',
    'human.you': '你',
    'human.inPos': '有位置',
    'human.oop': '无位置',

    'coach.title': '◈ AI 教练',
    'coach.thinking': '◈ AI 分析中...',
    'coach.recommend': '推荐：',
    'coach.empty': '点击 ◈ AI分析 获取建议',

    'showdown.label': '◈ 摊牌 ◈',

    // Learning Mode
    'learn.toggle': '学习',
    'learn.statsBtn': '📊 统计',
    'learn.hintTitle': '◈ GTO 提示',
    'learn.reviewTitle': '◈ 手牌复盘',
    'learn.netResult': '本手盈亏：',
    'learn.grade.correct': '正确',
    'learn.grade.marginal': '尚可',
    'learn.grade.mistake': '失误',
    'learn.caveat': '评分基于 GTO 基准近似，非求解器精确值，仅供参考。',
    'learn.statsTitle': '◈ 会话统计',
    'learn.statsEmpty': '打几手牌后即可查看统计数据。',
    'learn.handsPlayed': '手数',
    'learn.net': '盈亏',
    'learn.leaksTitle': '◈ 漏洞检测',
    'learn.leaksEmpty': '暂未检测到明显漏洞，继续加油。',

    // Setup lobby
    'setup.opponents': '对手数量',
    'setup.stack': '起始筹码',
    'setup.speed': '升盲速度',
    'setup.speed.turbo': '极速',
    'setup.speed.normal': '标准',
    'setup.speed.slow': '慢速',
    'setup.difficulty': '难度',
    'setup.diff.easy': '简单',
    'setup.diff.normal': '普通',
    'setup.diff.hard': '困难',

    // Tournament
    'tour.level': '级别',
    'tour.blinds': '盲注',
    'tour.nextLevel': '下一级',
    'tour.remaining': '存活',
    'tour.place': '排名',
    'tour.youWin': '🏆 你赢了！',
    'tour.over': '锦标赛结束',
    'tour.yourFinish': '你的名次',
    'tour.playAgain': '▶ 再来一局',
    'tour.blindsUp': '升盲',

    // All-in
    'allin.title': '全下胜率',

    // Career
    'career.button': '◈ 生涯',
    'career.title': '◈ 生涯',
    'career.empty': '还没有参赛记录，打一局开始记录吧。',
    'career.played': '参赛',
    'career.wins': '夺冠',
    'career.winRate': '胜率',
    'career.best': '最佳',
    'career.avg': '平均名次',
    'career.podiums': '前三',
    'career.achievements': '◈ 成就',

    'lang.select': '选择语言',
  },
};

export default locales;

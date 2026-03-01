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

    'lang.select': '选择语言',
  },
};

export default locales;

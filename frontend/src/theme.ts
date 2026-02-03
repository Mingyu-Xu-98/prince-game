// 浅色米色主题配置
export const theme = {
  // 背景色
  bg: {
    primary: '#FDF6E3',      // 主背景 - 米色
    secondary: '#F5EBDC',    // 次级背景 - 浅米色
    tertiary: '#EDE4D3',     // 三级背景 - 深米色
    card: '#FFFFFF',         // 卡片背景 - 白色
    hover: '#F0E6D2',        // 悬停背景
    input: '#FFFFFF',        // 输入框背景
    overlay: 'rgba(0, 0, 0, 0.4)', // 遮罩层
  },

  // 文字色
  text: {
    primary: '#3D3D3D',      // 主要文字 - 深灰
    secondary: '#6B6B6B',    // 次要文字 - 中灰
    muted: '#9B9B9B',        // 弱化文字 - 浅灰
    accent: '#8B6914',       // 强调文字 - 深金
    light: '#FFFFFF',        // 亮色文字
  },

  // 边框色
  border: {
    light: '#E8DCC8',        // 浅边框
    medium: '#D4C4A8',       // 中边框
    dark: '#B8A888',         // 深边框
  },

  // 强调色
  accent: {
    gold: '#C9A227',         // 金色 - 主强调
    goldLight: '#E8C547',    // 浅金
    goldDark: '#8B6914',     // 深金
    brown: '#8B4513',        // 棕色
  },

  // 顾问颜色
  advisor: {
    lion: '#C53030',         // 狮子 - 深红
    lionBg: '#FED7D7',       // 狮子背景
    fox: '#805AD5',          // 狐狸 - 紫色
    foxBg: '#E9D8FD',        // 狐狸背景
    balance: '#2F855A',      // 天平 - 深绿
    balanceBg: '#C6F6D5',    // 天平背景
  },

  // 状态颜色
  status: {
    success: '#38A169',      // 成功 - 绿
    successBg: '#C6F6D5',
    warning: '#D69E2E',      // 警告 - 黄
    warningBg: '#FEFCBF',
    error: '#E53E3E',        // 错误 - 红
    errorBg: '#FED7D7',
    info: '#3182CE',         // 信息 - 蓝
    infoBg: '#BEE3F8',
  },

  // 阴影
  shadow: {
    sm: '0 1px 3px rgba(0, 0, 0, 0.08)',
    md: '0 4px 12px rgba(0, 0, 0, 0.1)',
    lg: '0 10px 30px rgba(0, 0, 0, 0.12)',
  },
};

// 说话者配置 - 浅色主题
export const SPEAKER_CONFIG_LIGHT: Record<string, { icon: string; name: string; color: string; bgColor: string }> = {
  player: { icon: '👑', name: '君主', color: theme.accent.goldDark, bgColor: '#FEF3C7' },
  lion: { icon: '🦁', name: '狮子', color: theme.advisor.lion, bgColor: theme.advisor.lionBg },
  fox: { icon: '🦊', name: '狐狸', color: theme.advisor.fox, bgColor: theme.advisor.foxBg },
  balance: { icon: '⚖️', name: '天平', color: theme.advisor.balance, bgColor: theme.advisor.balanceBg },
  system: { icon: '📜', name: '系统', color: theme.text.secondary, bgColor: theme.bg.secondary },
};

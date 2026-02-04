// 最终审计结果面板 - 君主论风格报告

import type { FinalAudit } from '../types/game';
import { theme } from '../theme';

interface FinalAuditPanelProps {
  audit: FinalAudit;
  onNewGame: () => void;
}

// 根据玩家数据生成《君主论》风格的评价
function getMachiavelliAnalysis(audit: FinalAudit): {
  title: string;
  subtitle: string;
  analysis: string[];
  princeQuote: string;
  finalVerdict: string;
} {
  const { violence_ratio, deception_ratio, fairness_ratio, promise_reliability, reputation } = audit;

  // 狮子型君主 - 高暴力，低欺骗
  if (violence_ratio > 0.5 && deception_ratio < 0.3) {
    return {
      title: '雄狮之君',
      subtitle: '以力量与恐惧统治',
      analysis: [
        '你选择了狮子的道路——以力量震慑敌人，以恐惧维持秩序。',
        `在 ${audit.total_decisions} 次决策中，${audit.violent_decisions} 次选择了暴力手段，展现了果断而残酷的统治风格。`,
        violence_ratio > 0.7
          ? '然而，马基雅维利警告：纯粹的暴力终将招致叛乱。恐惧应当是统治的工具，而非目的。'
          : '你在威慑与克制之间保持了微妙的平衡，这是狮子型君主的最佳状态。',
        promise_reliability < 0.5
          ? '你的承诺如同虎口中的猎物——看似可靠，实则危险。这虽然务实，但也削弱了臣民的信任。'
          : '你重视自己的承诺，这为你赢得了些许尊重，但也可能成为敌人的把柄。'
      ],
      princeQuote: '君主必须学会如何不做善人，并根据需要使用或不使用这种本领。',
      finalVerdict: violence_ratio > 0.7
        ? '你是一位令人畏惧的君主，但要小心——过度的残暴会让恐惧转化为仇恨。'
        : '你掌握了狮子的力量而未被其吞噬，这是统治者的智慧。'
    };
  }

  // 狐狸型君主 - 高欺骗，低暴力
  if (deception_ratio > 0.5 && violence_ratio < 0.3) {
    return {
      title: '狡狐之君',
      subtitle: '以智谋与欺骗统治',
      analysis: [
        '你选择了狐狸的道路——以狡诈识破陷阱，以谎言编织权力。',
        `在 ${audit.total_decisions} 次决策中，${audit.deceptive_decisions} 次选择了欺骗手段，展现了老练的政治手腕。`,
        deception_ratio > 0.7
          ? '然而，马基雅维利提醒：谎言需要更多谎言来维持，直到它们自相矛盾。你的伪装能维持多久？'
          : '你在真假之间游走自如，让敌人永远猜不透你的真实意图——这正是狐狸的精髓。',
        audit.secrets_leaked > 2
          ? `但你的秘密泄露了 ${audit.secrets_leaked} 次，每一次都是权力的削弱。狡猾的狐狸也需要保守自己的巢穴。`
          : '你很好地保守了自己的秘密，这让你的谋略更加致命。'
      ],
      princeQuote: '人们总是如此天真，如此受眼前需要的支配，以至于一个想要欺骗的人总能找到愿意被欺骗的人。',
      finalVerdict: deception_ratio > 0.7
        ? '你是一位精于算计的君主，但谎言堆砌的王座终究不稳。'
        : '你掌握了欺骗的艺术却未沉溺其中，这是真正的政治智慧。'
    };
  }

  // 狮狐合一 - 高暴力且高欺骗
  if (violence_ratio > 0.4 && deception_ratio > 0.4) {
    return {
      title: '完美的君主',
      subtitle: '狮子与狐狸的结合',
      analysis: [
        '你同时掌握了狮子的力量和狐狸的狡诈——这正是马基雅维利所推崇的完美君主。',
        `${audit.violent_decisions} 次暴力决策震慑了敌人，${audit.deceptive_decisions} 次欺骗手段瓦解了阴谋。`,
        '你明白何时该露出獠牙，何时该隐藏意图。这种灵活性是统治的核心。',
        promise_reliability < 0.3
          ? '你从不被承诺束缚，因为你知道：在必要时，君主必须背弃诺言。'
          : '你在权谋与信义之间保持了某种平衡，这让你既可畏又可敬。'
      ],
      princeQuote: '君主必须知道如何同时扮演野兽和人。因此，必须成为狐狸以识别陷阱，成为狮子以吓退豺狼。',
      finalVerdict: '你真正理解了《君主论》的精髓——在道德与权力之间，选择有效的手段。这是最高的政治智慧。'
    };
  }

  // 明君型 - 高公正，低暴力低欺骗
  if (fairness_ratio > 0.5 && violence_ratio < 0.3 && deception_ratio < 0.3) {
    return {
      title: '仁德之君',
      subtitle: '以公正与美德统治',
      analysis: [
        '你选择了美德的道路——以公正赢得民心，以仁慈树立威望。',
        `在 ${audit.total_decisions} 次决策中，${audit.fair_decisions} 次选择了公正的方式，这让你赢得了臣民的爱戴。`,
        fairness_ratio > 0.7
          ? '然而，马基雅维利会质疑：在一个充满狼群的世界里，一只羔羊能存活多久？你的美德是否足以保护你？'
          : '你在仁慈与务实之间保持了智慧的平衡，既赢得爱戴也维持了尊重。',
        promise_reliability > 0.8
          ? '你的承诺比金子更可靠，这让你赢得了忠诚——但也可能成为敌人利用的弱点。'
          : '你知道何时遵守承诺，何时灵活变通，这是成熟的政治智慧。'
      ],
      princeQuote: '被人爱戴和被人畏惧，哪一种更好？回答是：两者兼得最好。但如果必须二选一，被畏惧比被爱戴更安全。',
      finalVerdict: fairness_ratio > 0.7
        ? '你是一位受人爱戴的君主，但马基雅维利会提醒你：爱戴建立在利益之上，恐惧才是更可靠的纽带。'
        : '你在公正与权谋之间找到了自己的道路，这是独特而有效的统治方式。'
    };
  }

  // 平庸之君 - 各项数据都比较平均
  if (reputation === '庸主') {
    return {
      title: '中庸之君',
      subtitle: '缺乏鲜明的统治风格',
      analysis: [
        '你的统治缺乏鲜明的特色——既不令人畏惧，也未赢得足够的爱戴。',
        `在 ${audit.total_decisions} 次决策中，你的选择摇摆不定，让臣民无法预测你的意图。`,
        '马基雅维利认为：优柔寡断是君主最大的敌人。不做选择，就是选择失败。',
        '一个没有立场的君主，既不能震慑敌人，也无法激励盟友。'
      ],
      princeQuote: '中间道路是最有害的，因为它既不能获得朋友的帮助，也不能避免敌人的伤害。',
      finalVerdict: '你需要找到属于自己的统治哲学——无论是狮子的力量、狐狸的智慧，还是美德的光环。'
    };
  }

  // 默认评价
  return {
    title: '复杂的君主',
    subtitle: '难以定义的统治风格',
    analysis: [
      '你的统治展现了复杂的特质，难以用简单的标签来定义。',
      `在 ${audit.total_decisions} 次决策中，你展现了多变的风格，时而强硬，时而狡诈，时而公正。`,
      '这种不可预测性本身也是一种权力——让敌人永远无法摸透你的底牌。',
      '但要记住：过于复杂的策略可能让你自己也迷失方向。'
    ],
    princeQuote: '命运是一个女人，要想控制她，就必须打她、推她。',
    finalVerdict: '你的统治方式独特而复杂，历史将对你做出最终的评判。'
  };
}

export function FinalAuditPanel({ audit, onNewGame }: FinalAuditPanelProps) {
  const machiavelliAnalysis = getMachiavelliAnalysis(audit);

  const getReputationColor = (reputation: string) => {
    switch (reputation) {
      case '明君': return theme.status.success;
      case '暴君': return theme.status.error;
      case '骗子': return theme.advisor.fox;
      case '庸主': return theme.text.muted;
      default: return theme.accent.gold;
    }
  };

  const getReputationEmoji = (reputation: string) => {
    switch (reputation) {
      case '明君': return '👑';
      case '暴君': return '🗡️';
      case '骗子': return '🎭';
      case '庸主': return '😐';
      default: return '⚖️';
    }
  };

  const formatPercent = (value: number) => `${(value * 100).toFixed(1)}%`;

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: theme.bg.primary,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '40px',
    }}>
      <div style={{
        maxWidth: '900px',
        width: '100%',
        backgroundColor: theme.bg.card,
        borderRadius: '16px',
        border: `1px solid ${theme.border.light}`,
        overflow: 'hidden',
        boxShadow: theme.shadow.lg,
      }}>
        {/* 头部 - 君主论风格标题 */}
        <div style={{
          padding: '48px 40px',
          textAlign: 'center',
          borderBottom: `1px solid ${theme.border.light}`,
          background: `linear-gradient(180deg, ${theme.bg.secondary} 0%, ${theme.bg.card} 100%)`,
        }}>
          <div style={{
            fontSize: '64px',
            marginBottom: '16px',
          }}>
            {getReputationEmoji(audit.reputation)}
          </div>
          <h1 style={{
            margin: 0,
            color: getReputationColor(audit.reputation),
            fontSize: '36px',
            fontWeight: 'bold',
          }}>
            {machiavelliAnalysis.title}
          </h1>
          <p style={{
            margin: '8px 0 0 0',
            color: theme.text.secondary,
            fontSize: '18px',
            fontStyle: 'italic',
          }}>
            {machiavelliAnalysis.subtitle}
          </p>
          <p style={{
            margin: '16px 0 0 0',
            color: theme.text.muted,
            fontSize: '14px',
          }}>
            基于《君主论》的统治评估报告
          </p>
        </div>

        {/* 总分 */}
        <div style={{
          padding: '32px',
          textAlign: 'center',
          borderBottom: `1px solid ${theme.border.light}`,
          display: 'flex',
          justifyContent: 'center',
          gap: '48px',
        }}>
          <div>
            <div style={{
              color: theme.accent.gold,
              fontSize: '56px',
              fontWeight: 'bold',
            }}>
              {audit.final_score}
            </div>
            <div style={{
              color: theme.text.secondary,
              fontSize: '14px',
            }}>
              统治评分
            </div>
          </div>
          <div style={{ borderLeft: `1px solid ${theme.border.light}`, paddingLeft: '48px' }}>
            <div style={{
              color: getReputationColor(audit.reputation),
              fontSize: '56px',
              fontWeight: 'bold',
            }}>
              {audit.reputation}
            </div>
            <div style={{
              color: theme.text.secondary,
              fontSize: '14px',
            }}>
              历史评价
            </div>
          </div>
        </div>

        {/* 马基雅维利分析 */}
        <div style={{
          padding: '32px 40px',
          borderBottom: `1px solid ${theme.border.light}`,
          backgroundColor: '#FFFBF5',
        }}>
          <h3 style={{
            margin: '0 0 20px 0',
            color: theme.accent.goldDark,
            fontSize: '16px',
            fontWeight: '600',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}>
            📜 马基雅维利的评语
          </h3>

          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
          }}>
            {machiavelliAnalysis.analysis.map((paragraph, index) => (
              <p key={index} style={{
                margin: 0,
                color: theme.text.primary,
                fontSize: '15px',
                lineHeight: '1.8',
                textAlign: 'justify',
              }}>
                {paragraph}
              </p>
            ))}
          </div>

          {/* 君主论引用 */}
          <div style={{
            marginTop: '24px',
            padding: '20px 24px',
            backgroundColor: theme.bg.card,
            borderLeft: `4px solid ${theme.accent.gold}`,
            borderRadius: '0 8px 8px 0',
          }}>
            <p style={{
              margin: 0,
              color: theme.text.secondary,
              fontSize: '14px',
              fontStyle: 'italic',
              lineHeight: '1.6',
            }}>
              "{machiavelliAnalysis.princeQuote}"
            </p>
            <p style={{
              margin: '8px 0 0 0',
              color: theme.text.muted,
              fontSize: '12px',
              textAlign: 'right',
            }}>
              —— 尼科洛·马基雅维利，《君主论》
            </p>
          </div>

          {/* 最终裁决 */}
          <div style={{
            marginTop: '24px',
            padding: '16px 20px',
            backgroundColor: theme.accent.goldLight + '30',
            borderRadius: '8px',
            border: `1px solid ${theme.accent.gold}40`,
          }}>
            <p style={{
              margin: 0,
              color: theme.accent.goldDark,
              fontSize: '15px',
              fontWeight: '500',
              lineHeight: '1.6',
            }}>
              <strong>最终评判：</strong>{machiavelliAnalysis.finalVerdict}
            </p>
          </div>
        </div>

        {/* 统计数据 */}
        <div style={{
          padding: '32px 40px',
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: '24px',
        }}>
          {/* 决策统计 */}
          <div style={{
            backgroundColor: theme.bg.secondary,
            borderRadius: '12px',
            padding: '20px',
            border: `1px solid ${theme.border.light}`,
          }}>
            <h3 style={{
              margin: '0 0 16px 0',
              color: theme.accent.goldDark,
              fontSize: '14px',
              fontWeight: '600',
            }}>
              📊 决策统计
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: theme.text.secondary }}>总决策数</span>
                <span style={{ color: theme.text.primary, fontWeight: '500' }}>{audit.total_decisions}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: theme.text.secondary }}>暴力决策（狮子）</span>
                <span style={{ color: theme.status.error, fontWeight: '500' }}>{audit.violent_decisions}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: theme.text.secondary }}>欺骗决策（狐狸）</span>
                <span style={{ color: theme.advisor.fox, fontWeight: '500' }}>{audit.deceptive_decisions}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: theme.text.secondary }}>公正决策（美德）</span>
                <span style={{ color: theme.status.success, fontWeight: '500' }}>{audit.fair_decisions}</span>
              </div>
            </div>
          </div>

          {/* 承诺统计 */}
          <div style={{
            backgroundColor: theme.bg.secondary,
            borderRadius: '12px',
            padding: '20px',
            border: `1px solid ${theme.border.light}`,
          }}>
            <h3 style={{
              margin: '0 0 16px 0',
              color: theme.accent.goldDark,
              fontSize: '14px',
              fontWeight: '600',
            }}>
              🤝 承诺记录
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: theme.text.secondary }}>承诺总数</span>
                <span style={{ color: theme.text.primary, fontWeight: '500' }}>{audit.promises_made}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: theme.text.secondary }}>违背承诺</span>
                <span style={{ color: theme.status.error, fontWeight: '500' }}>{audit.promises_broken}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: theme.text.secondary }}>承诺可靠度</span>
                <span style={{ color: audit.promise_reliability > 0.7 ? theme.status.success : theme.status.warning, fontWeight: '500' }}>
                  {formatPercent(audit.promise_reliability)}
                </span>
              </div>
            </div>
          </div>

          {/* 把柄与秘密 */}
          <div style={{
            backgroundColor: theme.bg.secondary,
            borderRadius: '12px',
            padding: '20px',
            border: `1px solid ${theme.border.light}`,
          }}>
            <h3 style={{
              margin: '0 0 16px 0',
              color: theme.accent.goldDark,
              fontSize: '14px',
              fontWeight: '600',
            }}>
              🔒 秘密与把柄
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: theme.text.secondary }}>秘密泄露</span>
                <span style={{ color: theme.status.error, fontWeight: '500' }}>{audit.secrets_leaked} 次</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: theme.text.secondary }}>被握把柄</span>
                <span style={{ color: theme.advisor.fox, fontWeight: '500' }}>{audit.leverages_held} 个</span>
              </div>
            </div>
          </div>

          {/* 比率统计 - 狮狐平衡 */}
          <div style={{
            backgroundColor: theme.bg.secondary,
            borderRadius: '12px',
            padding: '20px',
            border: `1px solid ${theme.border.light}`,
          }}>
            <h3 style={{
              margin: '0 0 16px 0',
              color: theme.accent.goldDark,
              fontSize: '14px',
              fontWeight: '600',
            }}>
              🦁🦊 狮狐平衡
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ color: theme.text.secondary }}>🦁 狮子（暴力）</span>
                  <span style={{ color: theme.status.error, fontWeight: '500' }}>{formatPercent(audit.violence_ratio)}</span>
                </div>
                <div style={{
                  height: '6px',
                  backgroundColor: theme.status.errorBg,
                  borderRadius: '3px',
                  overflow: 'hidden',
                }}>
                  <div style={{
                    width: `${audit.violence_ratio * 100}%`,
                    height: '100%',
                    backgroundColor: theme.status.error,
                  }} />
                </div>
              </div>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ color: theme.text.secondary }}>🦊 狐狸（欺骗）</span>
                  <span style={{ color: theme.advisor.fox, fontWeight: '500' }}>{formatPercent(audit.deception_ratio)}</span>
                </div>
                <div style={{
                  height: '6px',
                  backgroundColor: theme.advisor.foxBg,
                  borderRadius: '3px',
                  overflow: 'hidden',
                }}>
                  <div style={{
                    width: `${audit.deception_ratio * 100}%`,
                    height: '100%',
                    backgroundColor: theme.advisor.fox,
                  }} />
                </div>
              </div>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ color: theme.text.secondary }}>⚖️ 美德（公正）</span>
                  <span style={{ color: theme.status.success, fontWeight: '500' }}>{formatPercent(audit.fairness_ratio)}</span>
                </div>
                <div style={{
                  height: '6px',
                  backgroundColor: theme.status.successBg,
                  borderRadius: '3px',
                  overflow: 'hidden',
                }}>
                  <div style={{
                    width: `${audit.fairness_ratio * 100}%`,
                    height: '100%',
                    backgroundColor: theme.status.success,
                  }} />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 底部按钮 */}
        <div style={{
          padding: '24px 40px 40px',
        }}>
          <button
            onClick={onNewGame}
            style={{
              width: '100%',
              padding: '18px',
              backgroundColor: theme.accent.gold,
              color: '#fff',
              border: 'none',
              borderRadius: '8px',
              fontSize: '16px',
              fontWeight: 'bold',
              cursor: 'pointer',
              transition: 'all 0.2s',
              boxShadow: theme.shadow.sm,
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = theme.accent.goldDark;
              e.currentTarget.style.transform = 'translateY(-2px)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = theme.accent.gold;
              e.currentTarget.style.transform = 'translateY(0)';
            }}
          >
            🔄 开启新的统治
          </button>
        </div>
      </div>
    </div>
  );
}

// 游戏设置/开始界面组件

import { useState } from 'react';

interface SetupScreenProps {
  apiKey: string;
  onApiKeyChange: (key: string) => void;
  model: string;
  onModelChange: (model: string) => void;
  onStartGame: () => void;
  isLoading: boolean;
  error: string | null;
}

const AVAILABLE_MODELS = [
  { id: '', label: '默认 (Claude 3.5 Sonnet)' },
  { id: 'anthropic/claude-3.5-sonnet', label: 'Claude 3.5 Sonnet' },
  { id: 'anthropic/claude-3-opus', label: 'Claude 3 Opus' },
  { id: 'openai/gpt-4-turbo', label: 'GPT-4 Turbo' },
  { id: 'openai/gpt-4o', label: 'GPT-4o' },
  { id: 'google/gemini-pro-1.5', label: 'Gemini Pro 1.5' },
  { id: 'meta-llama/llama-3.1-70b-instruct', label: 'Llama 3.1 70B' },
];

export function SetupScreen({
  apiKey,
  onApiKeyChange,
  model,
  onModelChange,
  onStartGame,
  isLoading,
  error,
}: SetupScreenProps) {
  const [showApiKey, setShowApiKey] = useState(false);

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#0a0a14',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '40px 20px',
    }}>
      {/* 标题区 */}
      <div style={{
        textAlign: 'center',
        marginBottom: '40px',
      }}>
        <h1 style={{
          color: '#ffd700',
          fontSize: '42px',
          margin: '0 0 8px 0',
          fontWeight: '300',
          letterSpacing: '4px',
        }}>
          君 主 论
        </h1>
        <div style={{
          color: '#888',
          fontSize: '16px',
          letterSpacing: '2px',
        }}>
          THE PRINCE: A GAME OF POWER
        </div>
      </div>

      {/* 引言 */}
      <div style={{
        maxWidth: '600px',
        textAlign: 'center',
        marginBottom: '40px',
        padding: '24px',
        backgroundColor: '#1a1a2e',
        borderRadius: '8px',
        border: '1px solid #333',
      }}>
        <div style={{
          color: '#e0e0e0',
          fontSize: '15px',
          lineHeight: '1.8',
          fontStyle: 'italic',
        }}>
          "君主必须既是狮子又是狐狸——狮子不能使自己免于陷阱，而狐狸则不能抵御豺狼。"
        </div>
        <div style={{
          color: '#888',
          fontSize: '13px',
          marginTop: '12px',
        }}>
          —— 尼科洛·马基雅维利
        </div>
      </div>

      {/* 配置表单 */}
      <div style={{
        width: '100%',
        maxWidth: '450px',
        backgroundColor: '#1a1a2e',
        borderRadius: '12px',
        border: '1px solid #333',
        padding: '32px',
      }}>
        <h2 style={{
          color: '#fff',
          fontSize: '18px',
          margin: '0 0 24px 0',
          fontWeight: '500',
        }}>
          ⚙️ 游戏配置
        </h2>

        {/* API Key 输入 */}
        <div style={{ marginBottom: '20px' }}>
          <label style={{
            display: 'block',
            color: '#888',
            fontSize: '13px',
            marginBottom: '8px',
          }}>
            OpenRouter API Key *
          </label>
          <div style={{ position: 'relative' }}>
            <input
              type={showApiKey ? 'text' : 'password'}
              value={apiKey}
              onChange={(e) => onApiKeyChange(e.target.value)}
              placeholder="sk-or-..."
              style={{
                width: '100%',
                padding: '12px 40px 12px 16px',
                backgroundColor: '#0a0a14',
                border: '1px solid #333',
                borderRadius: '8px',
                color: '#fff',
                fontSize: '14px',
                outline: 'none',
                boxSizing: 'border-box',
              }}
            />
            <button
              type="button"
              onClick={() => setShowApiKey(!showApiKey)}
              style={{
                position: 'absolute',
                right: '12px',
                top: '50%',
                transform: 'translateY(-50%)',
                background: 'none',
                border: 'none',
                color: '#666',
                cursor: 'pointer',
                fontSize: '14px',
              }}
            >
              {showApiKey ? '🙈' : '👁️'}
            </button>
          </div>
          <div style={{
            fontSize: '12px',
            color: '#666',
            marginTop: '6px',
          }}>
            从{' '}
            <a
              href="https://openrouter.ai/keys"
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: '#3b82f6' }}
            >
              openrouter.ai
            </a>
            {' '}获取 API Key
          </div>
        </div>

        {/* 模型选择 */}
        <div style={{ marginBottom: '24px' }}>
          <label style={{
            display: 'block',
            color: '#888',
            fontSize: '13px',
            marginBottom: '8px',
          }}>
            AI 模型
          </label>
          <select
            value={model}
            onChange={(e) => onModelChange(e.target.value)}
            style={{
              width: '100%',
              padding: '12px 16px',
              backgroundColor: '#0a0a14',
              border: '1px solid #333',
              borderRadius: '8px',
              color: '#fff',
              fontSize: '14px',
              outline: 'none',
              cursor: 'pointer',
            }}
          >
            {AVAILABLE_MODELS.map((m) => (
              <option key={m.id} value={m.id}>
                {m.label}
              </option>
            ))}
          </select>
        </div>

        {/* 错误提示 */}
        {error && (
          <div style={{
            padding: '12px 16px',
            backgroundColor: '#2d1515',
            border: '1px solid #ef444450',
            borderRadius: '8px',
            color: '#fca5a5',
            fontSize: '13px',
            marginBottom: '20px',
          }}>
            ⚠️ {error}
          </div>
        )}

        {/* 开始按钮 */}
        <button
          onClick={onStartGame}
          disabled={!apiKey || isLoading}
          style={{
            width: '100%',
            padding: '14px',
            backgroundColor: !apiKey || isLoading ? '#333' : '#ffd700',
            color: !apiKey || isLoading ? '#666' : '#000',
            border: 'none',
            borderRadius: '8px',
            fontSize: '16px',
            fontWeight: 'bold',
            cursor: !apiKey || isLoading ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s',
          }}
        >
          {isLoading ? '正在准备...' : '开始统治 👑'}
        </button>
      </div>

      {/* 游戏说明 */}
      <div style={{
        maxWidth: '600px',
        marginTop: '40px',
        padding: '24px',
        backgroundColor: '#0f0f1a',
        borderRadius: '8px',
        border: '1px solid #222',
      }}>
        <h3 style={{
          color: '#ffd700',
          fontSize: '14px',
          margin: '0 0 16px 0',
        }}>
          📜 游戏规则
        </h3>
        <div style={{
          color: '#888',
          fontSize: '13px',
          lineHeight: '1.8',
        }}>
          <p style={{ margin: '0 0 12px 0' }}>
            作为新登基的君主，你将面对内忧外患。三位顾问将评判你的每一个决定：
          </p>
          <ul style={{ margin: 0, paddingLeft: '20px' }}>
            <li><span style={{ color: '#ef4444' }}>🦁 狮子</span> - 评估你的决策是否果断有力</li>
            <li><span style={{ color: '#f97316' }}>🦊 狐狸</span> - 检验你言行的一致性</li>
            <li><span style={{ color: '#22c55e' }}>⚖️ 天平</span> - 衡量政策对各阶层的影响</li>
          </ul>
          <p style={{ margin: '12px 0 0 0' }}>
            维持 <span style={{ color: '#3b82f6' }}>掌控力(A)</span>、
            <span style={{ color: '#ef4444' }}>畏惧值(F)</span>、
            <span style={{ color: '#22c55e' }}>爱戴值(L)</span> 的平衡，
            避免统治崩溃。
          </p>
        </div>
      </div>
    </div>
  );
}

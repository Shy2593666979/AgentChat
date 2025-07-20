<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { loginAPI } from '../../apis/auth'
import { useUserStore } from '../../store/user'

const router = useRouter()
const userStore = useUserStore()

const loginForm = reactive({
  username: '',
  password: ''
})

const loading = ref(false)

const handleLogin = async () => {
  if (!loginForm.username || !loginForm.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }

  try {
    loading.value = true
    const response = await loginAPI(loginForm)
    
    if (response.data.status_code === 200) {
      ElMessage.success('登录成功')
      
      // 使用store管理用户状态
      if (response.data.data?.access_token && response.data.data?.user_id) {
        userStore.setUserInfo(response.data.data.access_token, {
          id: response.data.data.user_id,
          username: loginForm.username
        })
      }
      
      // 跳转到主页
      router.push('/')
    } else {
      ElMessage.error(response.data.status_message || '登录失败')
    }
  } catch (error: any) {
    console.error('登录错误:', error)
    if (error.response?.data?.message) {
      ElMessage.error(error.response.data.status_message)
    } else if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('登录失败，请检查网络连接')
    }
  } finally {
    loading.value = false
  }
}

const goToRegister = () => {
  router.push('/register')
}
</script>

<template>
  <div class="login-container">
    <!-- 左侧3D图形区域 -->
    <div class="left-section">
      <div class="graphic-container">
        <div class="cube-3d">
          <div class="cube-face front"></div>
          <div class="cube-face back"></div>
          <div class="cube-face right"></div>
          <div class="cube-face left"></div>
          <div class="cube-face top"></div>
          <div class="cube-face bottom"></div>
        </div>
        <div class="cylinder-3d"></div>
        <div class="sphere-3d"></div>
      </div>
    </div>

    <!-- 右侧登录表单区域 -->
    <div class="right-section">
      <div class="login-form-container">
        <!-- Logo和标题 -->
        <div class="header">
          <div class="logo">
            <span class="logo-text">AgentChat</span>
          </div>
          <p class="subtitle">更智能、更多元的大模型应用开发平台</p>
        </div>

        <!-- 登录表单 -->
        <div class="login-form">
          <div class="form-group">
            <label class="form-label">账号</label>
            <el-input
              v-model="loginForm.username"
              placeholder="请输入账号"
              size="large"
              class="login-input"
              @keyup.enter="handleLogin"
            />
          </div>

          <div class="form-group">
            <label class="form-label">密码</label>
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              size="large"
              class="login-input"
              show-password
              @keyup.enter="handleLogin"
            />
          </div>

          <div class="form-actions">
            <div class="register-link">
              <span>没有账号？</span>
              <a href="#" @click="goToRegister">注册</a>
            </div>
          </div>

          <el-button
            type="primary"
            size="large"
            class="login-button"
            :loading="loading"
            @click="handleLogin"
          >
            登录
          </el-button>
        </div>

        <!-- 底部版本信息 -->
        <div class="footer">
          <span>v2.0.1</span>
          <div class="footer-icons">
            <a href="https://github.com/Shy2593666979/AgentChat" target="_blank">
              <i class="icon-github"></i>
            </a>
            <a href="#" target="_blank">
              <i class="icon-docs"></i>
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.login-container {
  display: flex;
  height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.left-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;

  .graphic-container {
    position: relative;
    width: 400px;
    height: 400px;
    
    .cube-3d {
      position: absolute;
      width: 120px;
      height: 120px;
      top: 50px;
      left: 100px;
      transform-style: preserve-3d;
      animation: rotateCube 10s infinite linear;

      .cube-face {
        position: absolute;
        width: 120px;
        height: 120px;
        background: linear-gradient(45deg, #4f81ff, #3b66db);
        border: 1px solid rgba(255, 255, 255, 0.2);
        
        &.front { transform: rotateY(0deg) translateZ(60px); }
        &.back { transform: rotateY(180deg) translateZ(60px); }
        &.right { transform: rotateY(90deg) translateZ(60px); }
        &.left { transform: rotateY(-90deg) translateZ(60px); }
        &.top { transform: rotateX(90deg) translateZ(60px); }
        &.bottom { transform: rotateX(-90deg) translateZ(60px); }
      }
    }

    .cylinder-3d {
      position: absolute;
      width: 80px;
      height: 160px;
      top: 200px;
      left: 50px;
      background: linear-gradient(180deg, #6b9eff, #4f81ff);
      border-radius: 40px;
      box-shadow: 0 10px 30px rgba(79, 129, 255, 0.3);
      animation: floatUp 6s ease-in-out infinite;
    }

    .sphere-3d {
      position: absolute;
      width: 60px;
      height: 60px;
      top: 120px;
      right: 80px;
      background: radial-gradient(circle at 30% 30%, #8bb6ff, #4f81ff);
      border-radius: 50%;
      box-shadow: 0 8px 25px rgba(79, 129, 255, 0.4);
      animation: floatDown 8s ease-in-out infinite;
    }
  }
}

.right-section {
  width: 450px;
  background: white;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: -2px 0 20px rgba(0, 0, 0, 0.1);

  .login-form-container {
    width: 320px;
    padding: 40px 0;

    .header {
      text-align: center;
      margin-bottom: 40px;

      .logo {
        margin-bottom: 16px;

        .logo-text {
          display: inline-block;
          background: linear-gradient(45deg, #4f81ff, #3b66db);
          color: white;
          padding: 12px 24px;
          border-radius: 8px;
          font-size: 20px;
          font-weight: 700;
          letter-spacing: 2px;
          font-family: 'SF Pro Display', 'Helvetica Neue', 'Arial', sans-serif;
          box-shadow: 0 4px 12px rgba(79, 129, 255, 0.3);
        }
      }

      .subtitle {
        color: #555;
        font-size: 16px;
        margin: 0;
        line-height: 1.6;
        font-weight: 400;
        font-family: 'PingFang SC', 'Helvetica Neue', 'Arial', sans-serif;
      }
    }

    .login-form {
      .form-group {
        margin-bottom: 20px;

        .form-label {
          display: block;
          font-size: 16px;
          font-weight: 600;
          color: #2c3e50;
          margin-bottom: 10px;
          font-family: 'PingFang SC', 'Helvetica Neue', 'Arial', sans-serif;
          letter-spacing: 0.5px;
        }

        .login-input {
          :deep(.el-input__wrapper) {
            background: #f8f9fc;
            border: 1px solid #e1e5e9;
            border-radius: 8px;
            padding: 12px 16px;
            box-shadow: none;

            &:hover {
              border-color: #4f81ff;
            }

            &.is-focus {
              border-color: #4f81ff;
              box-shadow: 0 0 0 3px rgba(79, 129, 255, 0.1);
            }
          }

          :deep(.el-input__inner) {
            color: #2c3e50;
            font-size: 16px;
            font-family: 'PingFang SC', 'Helvetica Neue', 'Arial', sans-serif;
            font-weight: 400;

            &::placeholder {
              color: #a0a0a0;
              font-size: 15px;
            }
          }
        }
      }

      .form-actions {
        display: flex;
        justify-content: flex-end;
        margin-bottom: 24px;

        .register-link {
          font-size: 15px;
          color: #666;
          font-family: 'PingFang SC', 'Helvetica Neue', 'Arial', sans-serif;

          a {
            color: #4f81ff;
            text-decoration: none;
            margin-left: 6px;
            font-weight: 500;
            transition: all 0.2s ease;

            &:hover {
              text-decoration: underline;
              color: #3b66db;
            }
          }
        }
      }

      .login-button {
        width: 100%;
        height: 52px;
        background: linear-gradient(45deg, #4f81ff, #3b66db);
        border: none;
        border-radius: 10px;
        font-size: 18px;
        font-weight: 600;
        font-family: 'PingFang SC', 'Helvetica Neue', 'Arial', sans-serif;
        letter-spacing: 1px;
        transition: all 0.3s ease;

        &:hover {
          transform: translateY(-1px);
          box-shadow: 0 8px 25px rgba(79, 129, 255, 0.3);
        }

        &:active {
          transform: translateY(0);
        }
      }
    }

    .footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 40px;
      color: #888;
      font-size: 14px;
      font-family: 'PingFang SC', 'Helvetica Neue', 'Arial', sans-serif;
      font-weight: 400;

      .footer-icons {
        display: flex;
        gap: 12px;

        a {
          width: 24px;
          height: 24px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #999;
          transition: color 0.2s ease;

          &:hover {
            color: #4f81ff;
          }

          .icon-github::before {
            content: "🐙";
            font-size: 16px;
          }

          .icon-docs::before {
            content: "📚";
            font-size: 16px;
          }
        }
      }
    }
  }
}

@keyframes rotateCube {
  0% { transform: rotateX(0deg) rotateY(0deg); }
  100% { transform: rotateX(360deg) rotateY(360deg); }
}

@keyframes floatUp {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-15px); }
}

@keyframes floatDown {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(10px); }
}
</style> 
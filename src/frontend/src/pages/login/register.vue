<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { registerAPI } from '../../apis/auth'
import type { RegisterForm } from '../../apis/auth'

const router = useRouter()

const registerForm = reactive<RegisterForm>({
  user_name: '',
  user_email: '',
  user_password: ''
})

const confirmPassword = ref('')
const loading = ref(false)

const validateForm = () => {
  if (!registerForm.user_name) {
    ElMessage.warning('请输入用户名')
    return false
  }
  
  if (registerForm.user_name.length > 20) {
    ElMessage.warning('用户名长度不应该超过20个字符')
    return false
  }
  
  if (!registerForm.user_password) {
    ElMessage.warning('请输入密码')
    return false
  }
  
  if (registerForm.user_password.length < 6) {
    ElMessage.warning('密码长度至少6个字符')
    return false
  }
  
  if (registerForm.user_password !== confirmPassword.value) {
    ElMessage.warning('两次输入的密码不一致')
    return false
  }
  
  if (registerForm.user_email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(registerForm.user_email)) {
    ElMessage.warning('请输入有效的邮箱地址')
    return false
  }
  
  return true
}

const handleRegister = async () => {
  if (!validateForm()) {
    return
  }

  try {
    loading.value = true
    const response = await registerAPI(registerForm)
    
    if (response.data.status_code === 200) {
      ElMessage.success('注册成功，请登录')
      // 跳转到登录页面
      router.push('/login')
    } else {
      ElMessage.error(response.data.status_message || '注册失败')
    }
  } catch (error: any) {
    console.error('注册错误:', error)
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('注册失败，请检查网络连接')
    }
  } finally {
    loading.value = false
  }
}

const goToLogin = () => {
  router.push('/login')
}
</script>

<template>
  <div class="register-container">
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

    <!-- 右侧注册表单区域 -->
    <div class="right-section">
      <div class="register-form-container">
        <!-- Logo和标题 -->
        <div class="header">
          <div class="logo">
            <span class="logo-text">AgentChat</span>
          </div>
          <p class="subtitle">创建您的账户，开始智能对话之旅</p>
        </div>

        <!-- 注册表单 -->
        <div class="register-form">
          <div class="form-group">
            <label class="form-label">用户名</label>
            <el-input
              v-model="registerForm.user_name"
              placeholder="请输入用户名（最多20个字符）"
              size="large"
              class="register-input"
              @keyup.enter="handleRegister"
            />
          </div>

          <div class="form-group">
            <label class="form-label">邮箱（可选）</label>
            <el-input
              v-model="registerForm.user_email"
              placeholder="请输入邮箱地址"
              size="large"
              class="register-input"
              @keyup.enter="handleRegister"
            />
          </div>

          <div class="form-group">
            <label class="form-label">密码</label>
            <el-input
              v-model="registerForm.user_password"
              type="password"
              placeholder="请输入密码（至少6个字符）"
              size="large"
              class="register-input"
              show-password
              @keyup.enter="handleRegister"
            />
          </div>

          <div class="form-group">
            <label class="form-label">确认密码</label>
            <el-input
              v-model="confirmPassword"
              type="password"
              placeholder="请再次输入密码"
              size="large"
              class="register-input"
              show-password
              @keyup.enter="handleRegister"
            />
          </div>

          <div class="form-actions">
            <div class="login-link">
              <span>已有账号？</span>
              <a href="#" @click="goToLogin">登录</a>
            </div>
          </div>

          <el-button
            type="primary"
            size="large"
            class="register-button"
            :loading="loading"
            @click="handleRegister"
          >
            注册
          </el-button>
        </div>

        <!-- 底部版本信息 -->
        <div class="footer">
          <span>v2.0</span>
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
.register-container {
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

  .register-form-container {
    width: 320px;
    padding: 40px 0;

    .header {
      text-align: center;
      margin-bottom: 30px;

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

    .register-form {
      .form-group {
        margin-bottom: 18px;

        .form-label {
          display: block;
          font-size: 16px;
          font-weight: 600;
          color: #2c3e50;
          margin-bottom: 8px;
          font-family: 'PingFang SC', 'Helvetica Neue', 'Arial', sans-serif;
          letter-spacing: 0.5px;
        }

        .register-input {
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
        margin-bottom: 20px;

        .login-link {
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

      .register-button {
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
      margin-top: 30px;
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
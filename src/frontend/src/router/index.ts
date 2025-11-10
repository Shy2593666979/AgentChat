// router/index.ts
import { createRouter, createWebHistory } from 'vue-router';
import ChatPage from '../pages/conversation/chatPage/chatPage.vue';
import NotFound from '../pages/notFound/index';
import Index from '../pages/index.vue'
import conversation from '../pages/conversation/conversation.vue';
import DefaultPage from '../pages/conversation/defaultPage/defaultPage.vue';
import Construct from '../pages/construct';
import Configuration from '../pages/configuration'
import Login from '../pages/login'
import { Register } from '../pages/login'
import Agent from '../pages/agent'
import AgentEditor from '../pages/agent/agent-editor.vue'
import McpServer from '../pages/mcp-server'
import Knowledge from '../pages/knowledge'
import KnowledgeFile from '../pages/knowledge/knowledge-file.vue'
import Tool from '../pages/tool'
import Model from '../pages/model'
import ModelEditor from '../pages/model/model-editor.vue'
import Profile from '../pages/profile'
import Homepage from '../pages/homepage'
import MarsChat from '../pages/mars'
import Workspace from '../pages/workspace/workspace.vue'
import WorkspacePage from '../pages/workspace/workspacePage/workspacePage.vue'
import WorkspaceDefaultPage from '../pages/workspace/defaultPage/defaultPage.vue'
import TaskGraphPage from '../pages/workspace/taskGraphPage/taskGraphPage.vue'
import Dashboard from '../pages/dashboard'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: Login,
    meta: {
      requiresAuth: false
    }
  },
  {
    path: '/register',
    name: 'register',
    component: Register,
    meta: {
      requiresAuth: false
    }
  },
  {
    path: '/workspace',
    name: 'workspace',
    component: Workspace,
    meta: {
      requiresAuth: true
    },
    children: [
      {
        path: '',
        name: 'workspaceDefaultPage',
        component: WorkspaceDefaultPage,
      },
      {
        path: 'workspacePage',
        name: 'workspacePage',
        component: WorkspacePage,
      }
    ]
  },
  {
    path: '/workspace/taskGraph',
    name: 'taskGraphPage',
    component: TaskGraphPage,
    meta: {
      requiresAuth: true
    }
  },
  {
    path: '/',
    redirect: '/workspace',
    name: 'index',
    component: Index,
    meta: {
      requiresAuth: true
    },
    children: [
      {
        path: '/homepage',
        name: 'homepage',
        component: Homepage,
        meta: {
          current: 'homepage'
        }
      },
      {
        path: '/conversation',
        name: 'conversation',
        component: conversation,
        meta: {
          current: 'conversation'
        },
        children: [
          {
            path: '/conversation/',
            name: 'defaultPage',
            component: DefaultPage,
          },
          {
            path: '/conversation/chatPage',
            name: 'chatPage',
            component: ChatPage,
          }
        ]
      },
      {
        path: '/construct',
        name: 'construct',
        meta: {
          current: 'construct'
        },
        component: Construct,
      },
      {
        path: '/configuration',
        name: 'configuration',
        meta: {
          current: 'configuration'
        },
        component: Configuration,
      },
      {
        path: '/agent',
        name: 'agent',
        meta: {
          current: 'agent'
        },
        component: Agent,
      },
      {
        path: '/agent/editor',
        name: 'agent-editor',
        meta: {
          current: 'agent'
        },
        component: AgentEditor,
      },
      {
        path: '/mcp-server',
        name: 'mcp-server',
        meta: {
          current: 'mcp-server'
        },
        component: McpServer,
      },
      {
        path: '/knowledge',
        name: 'knowledge',
        meta: {
          current: 'knowledge'
        },
        component: Knowledge,
      },
      {
        path: '/knowledge/:knowledgeId/files',
        name: 'knowledge-file',
        meta: {
          current: 'knowledge'
        },
        component: KnowledgeFile,
      },
      {
        path: '/tool',
        name: 'tool',
        meta: {
          current: 'tool'
        },
        component: Tool,
      },
      {
        path: '/model',
        name: 'model',
        meta: {
          current: 'model'
        },
        component: Model,
      },
      {
        path: '/model/editor',
        name: 'model-editor',
        meta: {
          current: 'model'
        },
        component: ModelEditor,
      },
      {
        path: '/profile',
        name: 'profile',
        meta: {
          current: 'profile'
        },
        component: Profile,
      },
      {
        path: '/mars',
        name: 'mars',
        meta: {
          current: 'mars'
        },
        component: MarsChat,
      },
      {
        path: '/dashboard',
        name: 'dashboard',
        meta: {
          current: 'dashboard'
        },
        component: Dashboard,
      }
    ]
  },
  {
    path: '/:catchAll(.*)',
    name: 'not-found',
    component: NotFound,
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes: routes as RouteRecordRaw[],
});

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token');
  
  // 如果目标路由需要认证
  if (to.meta.requiresAuth) {
    if (token) {
      // 已登录，允许访问
      next();
    } else {
      // 未登录，跳转到登录页
      next('/login');
    }
  } else {
    // 不需要认证的路由（如登录页）
    if (to.path === '/login' && token) {
      // 已登录用户访问登录页，重定向到主页
      next('/');
    } else {
      next();
    }
  }
});

export default router;

// router/index.ts
import { createRouter, createWebHistory } from 'vue-router';
import ChatPage from '../pages/conversation/chatPage/chatPage.vue';
import NotFound from '../pages/notFound/index';
import Index from '../pages/index.vue'
import conversation from '../pages/conversation/conversation.vue';
import DefaultPage from '../pages/conversation/defaultPage/defaultPage.vue';
import Construct from '../pages/construct';
import Configuration from '../pages/configuration'

const routes = [

  {
    path: '/',
    redirect: '/conversation/',
    name: 'index',
    component: Index,

    children: [
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
  routes,
});

export default router;

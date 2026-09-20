import { Routes } from '@angular/router';

import { authGuard, staffGuard } from './core/guards';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./pages/home/home').then((m) => m.Home),
  },
  {
    path: 'login',
    loadComponent: () => import('./pages/login/login').then((m) => m.Login),
  },
  {
    path: 'register',
    loadComponent: () => import('./pages/register/register').then((m) => m.Register),
  },
  {
    path: 'dashboard',
    component: undefined, // placeholder replaced below
    canActivate: [authGuard],
  },
  { path: '**', redirectTo: '' },
];

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
    loadComponent: () => import('./pages/dashboard/dashboard').then((m) => m.Dashboard),
    canActivate: [authGuard],
  },
  {
    path: 'apply',
    loadComponent: () => import('./pages/apply/apply').then((m) => m.Apply),
    canActivate: [authGuard],
  },
  {
    path: 'staff',
    loadComponent: () => import('./pages/staff/staff').then((m) => m.Staff),
    canActivate: [staffGuard],
  },
  { path: '**', redirectTo: '' },
];

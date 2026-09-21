import { Routes } from '@angular/router';
import { inject } from '@angular/core';

import {
  approverGuard,
  authGuard,
  adminGuard,
  inspectorGuard,
  officerGuard,
  staffGuard,
} from './core/guards';
import { AuthService } from './core/auth.service';

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
    path: 'businesses',
    loadComponent: () => import('./pages/businesses/businesses').then((m) => m.Businesses),
    canActivate: [authGuard],
  },
  {
    path: 'apply',
    loadComponent: () => import('./pages/apply/apply').then((m) => m.Apply),
    canActivate: [authGuard],
  },
  {
    // Lands each staff role on its own workspace.
    path: 'staff',
    pathMatch: 'full',
    redirectTo: () => inject(AuthService).homeRoute(),
  },
  {
    path: 'staff/review',
    loadComponent: () => import('./pages/staff/staff').then((m) => m.Staff),
    canActivate: [officerGuard],
  },
  {
    path: 'staff/inspections',
    loadComponent: () => import('./pages/staff/staff').then((m) => m.Staff),
    canActivate: [inspectorGuard],
  },
  {
    path: 'staff/approvals',
    loadComponent: () => import('./pages/staff/staff').then((m) => m.Staff),
    canActivate: [approverGuard],
  },
  {
    path: 'staff/admin',
    loadComponent: () => import('./pages/staff/staff').then((m) => m.Staff),
    canActivate: [adminGuard],
  },
  { path: '**', redirectTo: '' },
];

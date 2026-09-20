import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';

import { AuthService } from '../../core/auth.service';

@Component({
  imports: [RouterLink],
  selector: 'app-home',
  templateUrl: './home.html',
})
export class Home {
  protected readonly auth = inject(AuthService);
  protected readonly steps = [
    'Register your business details',
    'Submit your licence application',
    'Get inspected by your LGA',
    'Pay via GePG control number',
    'Receive your QR-verifiable licence',
  ];
  protected readonly features = [
    {
      icon: '📄',
      title: 'Online applications',
      body: 'Apply from anywhere, track every status change, and get SMS updates at each step.',
    },
    {
      icon: '💳',
      title: 'Pay with control numbers',
      body: 'Invoices are issued with official GePG control numbers — pay by mobile money, bank or agent.',
    },
    {
      icon: '🔐',
      title: 'QR-verified licences',
      body: 'Every licence carries a QR code that anyone can scan to confirm it is genuine and current.',
    },
  ];
}

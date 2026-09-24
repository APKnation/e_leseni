import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { TanzaniaGeoService } from '../../core/tanzania-geo.service';
import { AuthService } from '../../core/auth.service';

interface Faq {
  q: string;
  a: string;
}

@Component({
  imports: [RouterLink],
  selector: 'app-home',
  templateUrl: './home.html',
})
export class Home {
  protected readonly auth = inject(AuthService);
  private readonly geo = inject(TanzaniaGeoService);

  /** Live coverage numbers from the bundled Tanzania geo dataset. */
  protected readonly regionCount = this.geo.regions().length;
  protected readonly councilCount = this.geo
    .regions()
    .reduce((sum, region) => sum + this.geo.districts(region).length, 0);

  protected readonly steps = [
    { title: 'Apply online', body: 'Register your business and submit your licence application — no queueing at the council office.' },
    { title: 'Get inspected', body: 'Your LGA officer reviews the application and schedules a premises inspection.' },
    { title: 'Pay via control number', body: 'Once approved, pay the invoice using an official GePG control number — mobile money, bank or agent.' },
    { title: 'Receive your licence', body: 'Download a QR-verifiable licence that anyone can scan to confirm it is genuine and current.' },
  ];

  protected readonly features = [
    {
      title: 'Online applications',
      body: 'Apply from anywhere, track every status change, and get SMS updates at each step.',
    },
    {
      title: 'Pay with control numbers',
      body: 'Invoices are issued with official GePG control numbers — pay by mobile money, bank or agent.',
    },
    {
      title: 'QR-verified licences',
      body: 'Every licence carries a QR code that anyone can scan to confirm it is genuine and current.',
    },
    {
      title: 'All 31 regions covered',
      body: 'Ward-level coverage across every region — select your council and ward from official data.',
    },
    {
      title: 'USSD for basic phones',
      body: 'No smartphone? Apply and check your application status over USSD from any phone.',
    },
    {
      title: 'Role-based workflow',
      body: 'Dedicated workspaces for officers, inspectors and approvers keep every step accountable.',
    },
  ];

  protected readonly roleCards = [
    {
      title: 'Applicants',
      body: 'Register businesses, apply for licences, pay invoices and download QR-verifiable licences.',
      cta: 'Create an account',
      link: '/register',
    },
    {
      title: 'Licensing officers',
      body: 'Review submitted applications, schedule inspections, return or reject incomplete ones.',
      cta: 'Officer log in',
      link: '/login',
    },
    {
      title: 'Inspectors',
      body: 'See scheduled inspections, record pass/fail results with findings on site.',
      cta: 'Inspector log in',
      link: '/login',
    },
    {
      title: 'Approvers',
      body: 'Give final approval on inspected applications and trigger invoicing.',
      cta: 'Approver log in',
      link: '/login',
    },
  ];

  protected readonly faqs: Faq[] = [
    {
      q: 'How long does a licence application take?',
      a: 'Most applications are reviewed within a few working days. You get an SMS at every status change — review, inspection, approval and payment.',
    },
    {
      q: 'How do I pay my licence fee?',
      a: 'After approval you receive an invoice with an official GePG control number. Pay it via mobile money, bank transfer or any authorised agent.',
    },
    {
      q: 'How can someone verify my licence is genuine?',
      a: 'Every issued licence carries a QR code. Scanning it opens a public verification page showing the licence status, validity dates and holder.',
    },
    {
      q: 'I applied at the wrong council — what now?',
      a: 'Return to your dashboard, re-apply under the correct council once an officer returns your application for correction.',
    },
  ];

  protected readonly openFaq = signal<number | null>(0);

  protected toggleFaq(index: number): void {
    this.openFaq.update((current) => (current === index ? null : index));
  }
}

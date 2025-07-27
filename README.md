# Claude CRM - MAKE Literary Productions

A self-hosted nonprofit fundraising CRM designed specifically for MAKE Literary Productions, a Chicago-based arts and literary nonprofit. Built with Claude Code to demonstrate modern CRM capabilities for arts organizations.

## Features

- **Donor Management**: Comprehensive contact management with relationship tracking
- **Event Management**: Literary event management with attendance tracking
- **Email Integration**: Automated communication workflows with Mailchimp integration
- **Tax Compliance**: Automated IRS-compliant receipt generation
- **Analytics**: RFM analysis and donor segmentation
- **Role-Based Access**: Team collaboration with permission management

## Technology Stack

- **Backend**: Django 4.2 with PostgreSQL 15
- **Frontend**: Django templates with Bootstrap 5
- **Database**: PostgreSQL with JSONB for flexible data storage
- **Email**: Mailchimp integration for marketing automation
- **Payments**: Stripe integration for donation processing
- **Deployment**: Docker Compose for self-hosted deployment

## Quick Start

1. Clone the repository
2. Copy `.env.example` to `.env` and configure your settings
3. Run with Docker Compose:
   ```bash
   docker-compose up -d
   ```
4. Create a superuser:
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```
5. Access the application at http://localhost:8000

## Project Structure

```
make-crm/
├── make_crm/           # Django project settings
├── apps/
│   ├── contacts/       # Contact management
│   ├── events/         # Event management
│   ├── transactions/   # Donation tracking
│   ├── communications/ # Email and communications
│   ├── analytics/      # Reporting and analytics
│   └── users/          # User management and permissions
├── templates/          # Django templates
├── static/             # Static files (CSS, JS, images)
├── requirements.txt    # Python dependencies
└── docker-compose.yml  # Docker configuration
```

## License

MIT License - see LICENSE file for details.
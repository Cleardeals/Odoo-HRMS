# HR Recruitment - Comprehensive Guide

## Table of Contents

- [Overview](#overview)
- [Module Ecosystem](#module-ecosystem)
- [Core Features](#core-features)
- [Installation & Configuration](#installation--configuration)
- [User Guide](#user-guide)
  - [Job Position Management](#job-position-management)
  - [Applicant Management](#applicant-management)
  - [Recruitment Pipeline](#recruitment-pipeline)
  - [Talent Pool](#talent-pool)
  - [Skills Matching](#skills-matching)
  - [Communication Tools](#communication-tools)
  - [Website Integration](#website-integration)
- [Technical Reference](#technical-reference)
- [Workflows](#workflows)
- [Best Practices](#best-practices)
- [FAQ](#faq)

---

## Overview

The Odoo HR Recruitment system is a comprehensive Applicant Tracking System (ATS) designed to streamline the entire hiring process from job posting to employee onboarding. The system consists of multiple integrated modules that provide end-to-end recruitment management capabilities.

### Key Capabilities

✅ **Complete Applicant Tracking** - Manage candidates through customizable recruitment stages  
✅ **Multi-Channel Sourcing** - Receive applications via email, website, or manual entry  
✅ **Talent Pool Management** - Build and maintain a database of qualified candidates  
✅ **Skills-Based Matching** - Match candidates to positions based on skills and qualifications  
✅ **Interview Management** - Schedule interviews, send assessments, and track responses  
✅ **Communication Hub** - Email, SMS, and chatter integration for candidate engagement  
✅ **Website Job Board** - Publish jobs on your website with SEO optimization  
✅ **Analytics & Reporting** - Track recruitment metrics and hiring performance  
✅ **Automation** - Automated emails, stage transitions, and notifications  

### Business Benefits

- **Reduced Time-to-Hire** - Streamlined processes and automation
- **Better Candidate Experience** - Professional communication and timely updates
- **Improved Quality of Hire** - Skills matching and structured evaluation
- **Centralized Database** - All recruitment data in one place
- **Data-Driven Decisions** - Analytics and reporting capabilities
- **Scalable Process** - Supports startups to enterprises

---

## Module Ecosystem

The HR Recruitment functionality is delivered through a modular architecture:

| Module | Purpose | Key Features |
|--------|---------|--------------|
| **hr_recruitment** | Core recruitment engine | Applicant tracking, job management, recruitment pipeline, talent pools |
| **hr_recruitment_skills** | Skills-based recruitment | Skills matching, candidate scoring, skill transfer to employees |
| **hr_recruitment_survey** | Interview assessments | Send surveys/tests, track responses, automated invitations |
| **hr_recruitment_sms** | SMS communication | Send SMS to candidates, mass campaigns, delivery tracking |
| **website_hr_recruitment** | Website integration | Public job board, online applications, SEO optimization |

### Dependencies

```
hr_recruitment
├── hr (Base HR module)
├── calendar (Meeting scheduling)
├── utm (Campaign tracking)
├── attachment_indexation (Document search)
├── web_tour (Onboarding tours)
└── digest (KPI digests)

hr_recruitment_skills
├── hr_recruitment
└── hr_skills

hr_recruitment_survey
├── hr_recruitment
└── survey

hr_recruitment_sms
├── hr_recruitment
└── sms

website_hr_recruitment
├── hr_recruitment
└── website
```

---

## Core Features

### 1. Applicant Management

**Applicant Profile**
- **Basic Information**: Name, email, phone, LinkedIn profile
- **Contact Details**: Normalized email/phone, sanitized numbers
- **Job Application**: Applied position, department, company
- **Assignment**: Recruiter, interviewers, stage
- **Status Tracking**: Application status, priority, probability
- **Education**: Degree level, expected degree
- **Salary**: Expected vs proposed salary, benefits
- **Availability**: Start date availability
- **Documents**: CV/resume, cover letters, certificates
- **Communication**: Emails, meetings, notes, activities
- **Tags**: Categorization with multiple tags
- **Properties**: Custom fields based on job position

**Application Sources**
- Email gateway (dedicated email address per job)
- Website job applications
- Manual creation
- LinkedIn integration
- Job board platforms (Indeed, Jobsdb, etc.)
- Recruitment sources with UTM tracking

**Applicant Actions**
- Create employee (convert hired applicant to employee)
- Schedule meetings/interviews
- Send emails (templates or custom)
- Send SMS messages
- Archive/unarchive
- Refuse with reason
- Reset to first stage
- Add to talent pool
- Link to existing contact
- Create activities
- Attach documents
- Log notes

### 2. Job Position Management

**Job Configuration**
- **Basic Details**: Job title, department, company, recruiter
- **Location**: Office/workplace address
- **Description**: Rich text job description
- **Requirements**: Required skills, education level, experience
- **Interviewers**: Multiple interviewers per job
- **Properties**: Custom applicant properties per job
- **Recruitment Sources**: Multiple sources with UTM tracking
- **Email Alias**: Dedicated email for applications
- **Interview Forms**: Link survey/assessment templates
- **Publication**: Website publishing settings

**Job Tracking**
- Total applications (all time)
- Open applications (active)
- New applications (unopened)
- Hired count
- Documents count
- Activity tracking
- Favorite jobs
- Industry classification

**Job Actions**
- Publish to website
- Create recruitment sources
- Set up email alias
- Add interviewers
- Define required skills
- Create interview forms
- Add applicants from talent pool
- Archive/unarchive

### 3. Recruitment Pipeline

**Default Stages**
1. **New** - Initial application received
2. **Qualification** - Initial screening
3. **First Interview** - Phone/video screening
4. **Second Interview** - In-person interview
5. **Contract Proposal** - Offer extended
6. **Contract Signed** - Hired (creates employee)

**Stage Configuration**
- Stage name and sequence
- Job-specific stages (per-job customization)
- Email templates (auto-send on stage entry)
- Requirements documentation
- Fold/unfold in kanban
- Hire indicator (final stage)
- Rotting threshold (days before stale)
- Kanban legends (normal/blocked/done/waiting)

**Pipeline Features**
- Drag-drop stage transitions
- Stage duration tracking
- Rotting applicants detection
- Batch operations
- Stage-based email automation
- Custom stage requirements
- Per-job stage customization

**Kanban States**
- **Normal** - In progress
- **Done** - Ready to advance
- **Waiting** - Waiting on external factor
- **Blocked** - Issue preventing progress

### 4. Talent Pool

**Pool Management**
- Create multiple talent pools
- Pool manager assignment
- Pool descriptions
- Color coding
- Tags/categories
- Talent count tracking

**Talent Features**
- Add applicants to pools
- Create talents from applicants
- Link similar applicants (duplicate detection)
- Apply talents to jobs
- Bulk operations
- Skill tracking
- Historical applications

**Duplicate Detection**
- Email matching
- Phone matching
- LinkedIn profile matching
- Batch refuse duplicates
- Link duplicates to original

**Use Cases**
- Build pipeline for future roles
- Maintain rejected applicants
- Track passive candidates
- Re-engage previous applicants
- Silver medal candidates
- Referral database

### 5. Skills-Based Recruitment

**Skills Matching**
- Define required skills per job
- Define skill levels (beginner/intermediate/expert)
- Calculate match percentage
- Compare applicant vs job requirements
- Consider education degree
- Weighted skill scoring

**Applicant Skills**
- Current skills
- Expired skills/certifications
- Skill levels
- Skill types
- Expiration dates
- Certification management

**Matching Features**
- Matching skills (has required skills)
- Missing skills (lacks required skills)
- Overall match score (0-100%)
- Degree matching
- Find best candidates
- Skill-based search
- Ranking by match score

**Skill Transfer**
- Copy skills to employee on hire
- Maintain skill levels
- Preserve skill types
- Update skill dates

### 6. Interview & Assessment

**Survey Integration**
- Create interview forms/assessments
- Assign forms to job positions
- Send to applicants via email
- Track response completion
- Multiple responses per applicant
- Print responses
- Print blank forms

**Interview Scheduling**
- Schedule calendar meetings
- Link to applicants
- Multiple interviewers
- Share attachments
- Track meeting dates
- Meeting summary in kanban

**Invitations**
- Automated email invitations
- Custom deadline (default 15 days)
- Partner creation if needed
- Survey templates
- Response notifications

### 7. Communication Tools

**Email Integration**
- Chatter/messaging
- Email templates
- Stage-based automation
- Custom email composer
- Send to multiple applicants
- Attachment management
- Scheduled sending
- Email tracking

**Email Templates**
- Congratulations email
- Refusal email
- Stage-specific templates
- Survey invitation
- Custom templates

**SMS Integration**
- Send SMS to applicants
- Mass SMS campaigns
- Phone validation
- Delivery tracking
- SMS composer
- Log in chatter

**Activities**
- Create activities
- Activity plans
- Department filtering
- Schedule activities
- Activity tracking
- Reminders

### 8. Website Job Board

**Job Publishing**
- Publish/unpublish jobs
- SEO metadata
- Website multi-publishing
- Job URL slugs
- Publication date tracking
- Rich text descriptions

**Job Listing**
- Public career page
- Search functionality
- Filters:
  - Country
  - Department
  - Office/location
  - Contract type
  - Remote jobs
- Pagination
- Responsive design

**Online Applications**
- Application forms
- Direct submission
- Automatic stage assignment
- Validation
- Document uploads
- Form input filtering

**SEO Features**
- SEO-friendly URLs
- Meta descriptions
- Schema markup
- Website builder integration
- Full-text search

**UTM Tracking**
- Campaign tracking
- Medium tracking
- Source tracking
- URL parameters
- Recruitment source URLs

### 9. Analytics & Reporting

**Metrics Tracked**
- Days to assign (time to first contact)
- Days to hire (time to close)
- Delay to close
- Application counts
- Hire rates
- Stage duration
- Success probability
- New vs old applications

**Reports**
- Recruitment dashboard
- Applicant analysis
- Source effectiveness
- Hiring funnel
- Time-to-hire trends
- Cost per hire
- Quality of hire

**Digest Integration**
- New colleagues KPI
- Weekly/monthly digests
- Email notifications
- Custom KPIs

### 10. Document Management

**Document Features**
- Attachment storage
- Document indexation
- Resume/CV parsing
- Search in documents
- Document viewer
- Attachment count
- Document categories

**Indexed Documents**
- Resumes/CVs
- Cover letters
- Certificates
- Diplomas
- References
- Work samples
- Interview notes

### 11. Access Rights & Security

**User Groups**

**1. Recruitment Officer**
- Full access to applicants
- Full access to jobs
- Full access to stages
- Full access to talent pools
- Manage all settings
- Create/edit/delete all records

**2. Recruitment Interviewer**
- Read applicants
- Update assigned applicants
- Read-only jobs
- Read-only stages
- Cannot delete
- Limited configuration

**3. Recruitment Manager**
- Full stage access
- Configuration management
- User management
- Analytics access

**Security Features**
- Record rules per user group
- Company-based security
- Department-based security
- Multi-company support
- Access logs

---

## Installation & Configuration

### Prerequisites

```bash
# Required modules
- hr (Base HR)
- calendar
- utm
- attachment_indexation
- web_tour
- digest

# Optional modules
- hr_skills (for skills matching)
- survey (for interview forms)
- sms (for SMS communication)
- website (for job board)
```

### Installation Steps

1. **Install Base Module**
   ```
   Apps → Search "Recruitment"
   Click "Install" on "Recruitment"
   ```

2. **Install Extensions** (Optional)
   ```
   Apps → Search "Recruitment"
   Install:
   - Recruitment: Skills
   - Recruitment: Survey Integration
   - Recruitment: SMS
   - Recruitment: Website Integration
   ```

### Initial Configuration

#### 1. Configure Recruitment Settings

Navigate to: `Recruitment → Configuration → Settings`

**Email Configuration**
- ✅ Enable email gateway
- ✅ Configure company email
- ✅ Set up SMTP server
- Configure email templates

**Recruitment Options**
- ✅ Enable talent pools
- ✅ Enable skills matching (requires hr_skills)
- ✅ Configure rotting threshold
- Set up applicant properties

**Website Options** (if website module installed)
- ✅ Enable job publishing
- Configure SEO settings
- Set up job board URL

#### 2. Set Up Recruitment Stages

Navigate to: `Recruitment → Configuration → Stages`

**Create/Customize Stages:**
```
Stage: New
├── Sequence: 0
├── Email Template: None
├── Requirements: Review application
└── Hired Stage: No

Stage: Qualification
├── Sequence: 1
├── Email Template: Acknowledgment email
├── Requirements: Initial screening
└── Hired Stage: No

Stage: First Interview
├── Sequence: 2
├── Email Template: Interview invitation
├── Requirements: Phone/video screening
└── Hired Stage: No

Stage: Second Interview
├── Sequence: 3
├── Email Template: Second interview invitation
├── Requirements: In-person interview
└── Hired Stage: No

Stage: Contract Proposal
├── Sequence: 4
├── Email Template: Offer letter
├── Requirements: Prepare offer
└── Hired Stage: No

Stage: Contract Signed
├── Sequence: 5
├── Email Template: Welcome email
├── Requirements: Signed contract received
└── Hired Stage: Yes (Creates employee)
```

#### 3. Configure Education Degrees

Navigate to: `Recruitment → Configuration → Degrees`

**Default Degrees:**
- Graduate (Score: 0.50)
- Bachelor Degree (Score: 0.70)
- Master Degree (Score: 0.90)
- Doctoral Degree (Score: 1.00)

**Custom Degrees:**
Add industry-specific degrees or certifications

#### 4. Set Up Refusal Reasons

Navigate to: `Recruitment → Configuration → Refusal Reasons`

**Default Reasons:**
- Does not fit job requirements
- Refused by applicant: job fit
- Job already fulfilled
- Duplicate application
- Spam
- Refused by applicant: salary

**Email Templates:**
Assign email templates to each refusal reason

#### 5. Configure Applicant Tags

Navigate to: `Recruitment → Configuration → Tags`

**Suggested Tags:**
- Reserve/Silver medal
- Manager potential
- IT/Technical
- Sales
- Remote worker
- Relocatable
- Referral
- Premium candidate

#### 6. Set Up Job Platforms

Navigate to: `Recruitment → Configuration → Job Platforms`

**Pre-configured Platforms:**
- LinkedIn (jobs-listings@linkedin.com)
- Jobsdb (cs@jobsdb.com)
- Indeed (no-reply@indeed.com)

**Add Custom Platforms:**
- Name: Platform name
- Email: Platform email address
- Regex: Name extraction pattern (optional)

#### 7. Configure Email Aliases

Navigate to: `Settings → Technical → Email → Aliases`

**System Alias:**
- Create catchall alias for recruitment
- Route to hr.applicant model
- Example: jobs@company.com

**Job-Specific Aliases:**
- Automatically created per job
- Format: job-{job_id}@company.com
- Routes to specific job position

#### 8. Set Up UTM Campaigns

Navigate to: `Recruitment → Configuration → UTM Campaigns`

**Create Campaigns:**
```
Campaign: Campus Recruitment 2026
├── Medium: Event
└── Sources: University A, University B

Campaign: LinkedIn Jobs
├── Medium: Social Media
└── Source: LinkedIn

Campaign: Job Fair Spring 2026
├── Medium: Event
└── Sources: Tech Fair, Career Expo
```

---

## User Guide

### Job Position Management

#### Creating a Job Position

1. **Navigate to Jobs**
   ```
   Recruitment → Jobs → Create
   ```

2. **Fill Basic Information**
   ```
   Job Title: Senior Software Engineer
   Department: Engineering
   Recruiter: John Doe
   No. of Recruitment: 2
   ```

3. **Set Job Location**
   ```
   Workplace Address: Select office location
   Remote Work: Check if applicable
   ```

4. **Add Job Description**
   ```
   Description Tab:
   - Job summary
   - Key responsibilities
   - Required qualifications
   - Benefits
   - Application instructions
   ```

5. **Define Requirements** (Skills Module)
   ```
   Requirements Tab:
   - Add required skills
   - Set skill levels
   - Expected degree
   ```

6. **Assign Interviewers**
   ```
   Interviewers Tab:
   - Add all interviewers
   - Grants them access to applicants
   ```

7. **Configure Email**
   ```
   Recruitment Tab:
   ✓ Email alias auto-created
   - senior-software-engineer-{id}@company.com
   ```

8. **Set Up Recruitment Sources**
   ```
   Recruitment Tab → Add Source:
   - Source: LinkedIn
   - Campaign: Q1 Tech Hiring
   - Medium: Social Media
   - Gets unique URL with UTM parameters
   ```

9. **Add Interview Form** (Survey Module)
   ```
   Recruitment Tab:
   - Interview Form: Select survey
   - Or create new assessment
   ```

10. **Publish to Website** (Website Module)
    ```
    Website Published: ✓ Check
    Website Description: Add SEO-friendly description
    Save → Go to Website
    ```

#### Managing Job Positions

**View All Applications**
```
Jobs → Select Job → Applications smart button
```

**Add Applicants from Talent Pool**
```
Jobs → Select Job → Add Applicants
- Select talent pool
- Choose applicants
- Set initial stage
- Create
```

**Modify Stages**
```
Jobs → Select Job → Stages
- Create job-specific stages
- Or use default stages
```

**Track Metrics**
```
Jobs → Kanban/List View:
- Total applications
- New applications
- Hired count
- Open positions
```

**Archive Job**
```
Jobs → Select Job → Action → Archive
- Stops new applications
- Hides from website
- Preserves data
```

### Applicant Management

#### Receiving Applications

**1. Via Email**
```
Applicant sends email to:
jobs@company.com (general)
OR
senior-software-engineer-5@company.com (specific job)

System automaticity:
✓ Creates applicant record
✓ Assigns to job (if job-specific email)
✓ Sets initial stage
✓ Extracts email/phone
✓ Attaches CV/documents
✓ Creates partner if needed
✓ Logs in chatter
```

**2. Via Website**
```
Candidate applies on career page:
Website → Careers → Job → Apply

Form captures:
- Name
- Email
- Phone
- LinkedIn
- Resume upload
- Cover letter
- Additional questions

System creates applicant automatically
```

**3. Manual Creation**
```
Recruitment → Applications → Create

Fill form:
- Subject: Application title
- Applicant's Name
- Email
- Phone
- Applied Job
- Department
- Recruiter
- Stage
- Expected Salary
- Degree
- Tags
- Attach documents
```

**4. Import Applications**
```
Recruitment → Applications → Favorites → Import Records
- Import CSV/Excel
- Map fields
- Validate data
- Import
```

#### Managing Applicants

**View Modes**

**Kanban View** (Default)
```
Recruitment → Applications → Kanban

Features:
- Drag-drop between stages
- Color-coded priorities
- Meeting indicators
- Quick info cards
- Batch select
```

**List View**
```
Recruitment → Applications → List

Columns:
- Subject
- Applicant Name
- Job Position
- Department
- Recruiter
- Stage
- Priority
- Create Date
- Last Update
```

**Calendar View**
```
Recruitment → Applications → Calendar

Shows:
- Scheduled interviews
- Availability dates
- Meeting dates
```

**Graph View**
```
Recruitment → Applications → Graph

Charts:
- Applications over time
- Applications by stage
- Applications by source
- Hire rate trends
```

**Pivot View**
```
Recruitment → Applications → Pivot

Analysis:
- Multi-dimensional analysis
- Custom grouping
- Export to Excel
```

#### Applicant Actions

**1. Schedule Interview**
```
Applicant → Schedule Meeting

Fill form:
- Meeting Subject
- Start Date/Time
- Duration
- Attendees (interviewers)
- Description
- Attach documents

✓ Creates calendar event
✓ Sends invitations
✓ Logs in chatter
```

**2. Send Email**
```
Applicant → Send Email

Options:
A. Use Template:
   - Select template
   - Preview/edit
   - Attach documents
   - Send

B. Custom Email:
   - Compose message
   - Add attachments
   - Send or schedule

✓ Logs in chatter
✓ Notifies applicant
```

**3. Send SMS** (SMS Module)
```
Applicant → Send SMS

- Enter message
- Preview
- Send

✓ Validates phone number
✓ Logs in chatter
✓ Tracks delivery
```

**4. Send Interview Form** (Survey Module)
```
Applicant → Send Interview

- Survey Template: Select
- Deadline: Set (default 15 days)
- Email: Auto-composed
- Send

✓ Creates survey invitation
✓ Generates unique link
✓ Sends email
✓ Tracks response
✓ Notifies on completion
```

**5. Refuse with Reason**
```
Applicant → Refuse

Select reason:
- Does not fit requirements
- Salary mismatch
- Duplicate
- Other

Options:
✓ Send email to applicant
✓ Send template email
✓ Schedule send

Result:
- Stage: Refused
- Application closed
- Email sent (optional)
```

**6. Create Employee**
```
Applicant → Create Employee

Available when:
- Stage marked as "Hired"
- Or manual creation

System creates:
✓ Employee record
✓ Copies basic info
✓ Transfers attachments
✓ Copies skills
✓ Links applicant to employee
✓ Closes application
```

**7. Add to Talent Pool**
```
Applicant → Action → Add to Talent Pool

Select:
- Talent Pool: Choose/create
- Tags: Add tags

Result:
✓ Creates talent record
✓ Links to applicant
✓ Available for future jobs
```

**8. Archive/Unarchive**
```
Applicant → Action → Archive

Effect:
- Removes from active view
- Closes application
- Preserves data
- Reversible (Unarchive)
```

**9. Reset to First Stage**
```
Applicant → Reset Applicant

Effect:
- Returns to first stage
- Clears refuse reason
- Reopens application
- Preserves history
```

**10. Link to Contact**
```
Applicant → Partner field → Select/Create

Links to:
- Existing contact
- OR creates new partner

Syncs:
- Email
- Phone
- Address
```

#### Batch Operations

**Refuse Multiple Applicants**
```
Applications → Select multiple → Action → Refuse

Options:
- Select refusal reason
- Choose email template
- Send email to all
- Refuse duplicates
```

**Send Mass Email**
```
Applications → Select multiple → Action → Send Email

Features:
- Template rendering per applicant
- Personalized emails
- Batch sending
- Attachment management
```

**Send Mass SMS**
```
Applications → Select multiple → Action → Send SMS

Features:
- Compose message
- Send to all selected
- Phone validation
- Delivery tracking
```

**Change Stage**
```
Applications → Select multiple → Drag to new stage

Or:
Applications → Select multiple → Action → Set Stage
```

**Add Tags**
```
Applications → Select multiple → Action → Add Tags
- Select tags
- Apply to all
```

**Export Data**
```
Applications → Select all/some → Action → Export
- Select fields
- Export format (CSV/Excel)
- Download
```

### Recruitment Pipeline

#### Working with Stages

**Stage Progression**
```
Drag Applicant Card → Drop on New Stage

Automated:
✓ Stage updated
✓ Date logged
✓ Email sent (if template configured)
✓ Activity created (if configured)
✓ Chatter message logged
```

**Stage Configuration**
```
Configuration → Stages → Select Stage

Settings:
- Name: Stage name
- Sequence: Order
- Requirements: Stage requirements/description
- Template: Email template to send
- Folded: Hide in kanban
- Hired Stage: Mark as final/hired stage
- Rotting Days: Days before marked stale
- Job IDs: Job-specific stages
- Legends: Customize kanban state labels
```

**Per-Job Stages**
```
Jobs → Select Job → Stages

Configure:
- Use default stages
- OR create job-specific stages
- Customize requirements
- Set job-specific email templates
```

**Kanban States**
```
On Applicant Card → Click stoplight icon

States:
🟢 Normal: In progress
🔵 Done: Ready for next stage
🟡 Waiting: Blocked by external factor
🔴 Blocked: Issue preventing progress

Use for:
- Visual indicators
- Filter applicants
- Identify bottlenecks
```

#### Pipeline Analytics

**Stage Duration**
```
Applications → Pivot View

Group by:
- Stage
- Date ranges

Metrics:
- Average days in stage
- Total applicants per stage
- Conversion rates
```

**Funnel Analysis**
```
Applications → Graph View → Bar Chart

X-axis: Stage
Y-axis: Count

Shows:
- Drop-off between stages
- Bottleneck stages
- Conversion funnel
```

**Rotting Applicants**
```
Applications → Filters → Rotting

Shows applicants:
- Exceeding stage threshold
- Require attention
- At risk of abandonment
```

### Talent Pool

#### Creating Talent Pools

```
Recruitment → Talent Pools → Create

Fields:
- Name: Pool title (e.g., "Software Engineers Q1")
- Pool Manager: Assigned person
- Description: Pool purpose
- Color: Color code
- Tags: Categorization
```

**Example Pools:**
- Silver Medal Candidates
- Future Leadership
- Technical Experts
- Sales Professionals
- Campus Recruits 2026
- Referrals Database
- Remote Workers
- Passive Candidates

#### Adding to Talent Pool

**Method 1: From Applicant**
```
Applicant → Action → Add to Talent Pool
- Select pool
- Add tags
- Create
```

**Method 2: Bulk Add**
```
Applications → Select multiple → Action → Add to Talent Pool
- Select pool
- Add tags
- Create talents
```

**Method 3: From Talent Pool**
```
Talent Pool → Add Applicants
- Search/filter applicants
- Select applicants
- Add tags
- Add to pool
```

#### Managing Talents

**View Talents**
```
Talent Pool → Talents smart button

Shows:
- All talents in pool
- Skills
- Previous applications
- Contact info
- Tags
```

**Duplicate Management**
```
Talent Pool → Find Duplicates

Detects duplicates by:
- Email match
- Phone match
- LinkedIn match

Actions:
- Link duplicates
- Refuse duplicates
- Merge records
```

**Apply to Job**
```
Talent Pool → Apply to Job

Steps:
1. Select talents
2. Choose job position
3. Set initial stage
4. Create applications

Result:
✓ Applications created
✓ Talent linked
✓ Stage assigned
```

#### Talent Pool Use Cases

**1. Build Future Pipeline**
```
Scenario: Not hiring now, but candidate is good

Flow:
1. Refuse applicant (kind message)
2. Add to "Future [Role]" pool
3. Add relevant tags
4. When position opens → apply to job
```

**2. Silver Medal Tracking**
```
Scenario: Great candidate, but position filled

Flow:
1. Reach final stage
2. Add to "Silver Medal" pool
3. Tag with skills/specialties
4. First to contact for similar roles
```

**3. Referral Database**
```
Scenario: Employee referrals

Flow:
1. Mark with "Referral" tag
2. Add to "Referrals" pool
3. Track referrer in notes
4. Priority for future openings
```

**4. Campus Recruitment**
```
Scenario: Campus hiring events

Flow:
1. Create "Campus [Year]" pool
2. Add all interviewed students
3. Tag by university/degree
4. Apply to internships/entry roles
```

### Skills Matching

**Prerequisites:**
- hr_recruitment_skills module installed
- hr_skills module installed
- Skills and skill types configured

#### Setting Up Skills

**1. Configure Skill Types**
```
Employees → Configuration → Skill Types

Examples:
- Programming Languages
- Frameworks
- Tools & Technologies
- Soft Skills
- Certifications
- Languages
```

**2. Create Skills**
```
Employees → Configuration → Skills

For each skill:
- Name: Skill name
- Skill Type: Category
- Levels: Beginner/Intermediate/Expert
```

**3. Define Job Requirements**
```
Jobs → Select Job → Requirements Tab

Add Required Skills:
- Skill: Select skill
- Level: Required proficiency
- Save
```

#### Recording Applicant Skills

**Method 1: Manual Entry**
```
Applicant → Skills Tab → Add Skill

Fields:
- Skill: Select skill
- Level: Proficiency level
- Valid To: Expiration (for certifications)
```

**Method 2: Import from Resume**
```
Future: Automatic skill extraction from CV
Currently: Manual review and entry
```

**Method 3: From Survey**
```
Survey Module:
- Create skills assessment
- Applicant completes
- Results create skill records
```

#### Matching & Scoring

**View Match Score**
```
Applicant → Skills Tab

Displays:
- Matching Skills: ✓ Green checkmarks
- Missing Skills: ✗ Red X marks
- Match Score: 0-100%
- Degree Match: Included in score
```

**Calculation Formula**
```
Match Score = (Matching Skills + Degree Match) / Total Requirements × 100

Example:
Job requires:
- Python (Expert)
- Django (Intermediate)
- PostgreSQL (Intermediate)
- Bachelor's Degree

Applicant has:
- Python (Expert) ✓
- Django (Beginner) ✗ (level mismatch)
- PostgreSQL (Intermediate) ✓
- Master's Degree ✓✓

Score = (2 skills + degree bonus) / 4 = 75%
```

**Find Best Candidates**
```
Applications → Filters → Add Custom Filter

Filter by:
- Matching Score > 70%
- Has required skills
- Missing skills < 2

Sort by:
- Matching Score (descending)
```

#### Skills Transfer on Hire

**Automatic Transfer**
```
When creating employee from applicant:

✓ All current skills copied
✓ Skill levels preserved
✓ Skill types maintained
✓ Expiration dates transferred
✓ Expired skills excluded
```

**Manual Review**
```
Option to:
- Review skills before transfer
- Update skill levels
- Add new skills
- Remove outdated skills
```

### Communication Tools

#### Email Communication

**1. Using Email Templates**

**Acknowledgment Email**
```
Stage: New → Qualification

Auto-sent when moved to Qualification:

Subject: Application Received - [Job Title]

Body:
Dear [Name],

Thank you for applying to [Job Title] at [Company].

We have received your application and will review it 
shortly. If your qualifications match our requirements, 
we will contact you for next steps.

Best regards,
[Recruiter Name]
```

**Interview Invitation**
```
Stage: Qualification → First Interview

Template:

Subject: Interview Invitation - [Job Title]

Dear [Name],

We are pleased to invite you for an interview for the 
[Job Title] position.

Interview Details:
- Date: [Meeting Date]
- Time: [Meeting Time]
- Duration: [Duration]
- Location/Link: [Location]
- Interviewers: [Interviewers]

Please confirm your availability.

Best regards,
[Recruiter Name]
```

**Offer Letter**
```
Stage: Contract Proposal

Template:

Subject: Job Offer - [Job Title]

Dear [Name],

We are delighted to offer you the position of [Job Title] 
at [Company].

Offer Details:
- Position: [Job Title]
- Department: [Department]
- Start Date: [Date]
- Salary: [Proposed Salary]
- Benefits: [Benefits]

Please review the attached offer letter and let us know 
your decision by [Deadline].

Congratulations!
[Recruiter Name]
```

**Refusal Email**
```
Refuse Action → Send Email

Template:

Subject: Application Update - [Job Title]

Dear [Name],

Thank you for your interest in [Job Title] at [Company] 
and for taking the time to interview with us.

After careful consideration, we have decided to move 
forward with other candidates whose qualifications more 
closely match our current needs.

We appreciate your interest and wish you the best in 
your job search.

Best regards,
[Recruiter Name]
```

**2. Custom Email Composer**
```
Applicant → Send Email → Custom

Fields:
- Recipients: Applicant email (auto-filled)
- Subject: Custom subject
- Body: Rich text editor
- Attachments: Add files
- Template: Optional (apply template)
- Schedule: Send now/later

Features:
- HTML formatting
- Dynamic placeholders
- Attachment management
- Template variables
- Save as template
```

**3. Batch Email Sending**
```
Applications → Select multiple → Send Email

Features:
- Template selection
- Per-applicant rendering
- Personalized variables
- Preview before send
- Scheduled sending
- Delivery tracking
```

**4. Email Placeholders**
```
Available variables in templates:

${object.partner_name} - Applicant name
${object.job_id.name} - Job title
${object.department_id.name} - Department
${object.user_id.name} - Recruiter name
${object.salary_proposed} - Proposed salary
${object.company_id.name} - Company name
${object.meeting_display_date} - Meeting date
```

#### SMS Communication

**Requirements:**
- hr_recruitment_sms module installed
- SMS gateway configured
- Credits available

**1. Send Individual SMS**
```
Applicant → Send SMS

Composer:
- Phone: Auto-filled (validated)
- Message: Type message (160 char limit)
- Preview: See final message
- Send

Result:
✓ SMS sent
✓ Logged in chatter
✓ Delivery status tracked
```

**2. Mass SMS Campaign**
```
Applications → Select multiple → SMS

Features:
- Compose message
- Preview recipients
- Phone validation
- Send to all valid numbers
- Skip invalid numbers
- Bulk delivery tracking
```

**3. SMS Use Cases**
```
Interview Reminder:
"Hi [Name], reminder of your interview tomorrow at [Time] 
for [Job]. Location: [Address]. See you there!"

Quick Update:
"Hi [Name], we've reviewed your application for [Job] and 
would like to schedule a call. Please check your email."

Offer Accepted:
"Congratulations [Name]! We're excited to have you join 
our team. Welcome aboard!"
```

#### Activity Management

**1. Create Activity**
```
Applicant → Schedule Activity

Fields:
- Activity Type: To-do/Call/Meeting/Email
- Summary: Activity title
- Assigned to: User
- Due Date: Deadline
- Notes: Additional info

Use cases:
- Follow-up calls
- Document requests
- Reference checks
- Background verification
```

**2. Activity Plans**
```
Configuration → Activity Plans

Create plan:
- Name: Plan name (e.g., "Interview Process")
- Activities:
  1. Schedule phone screen (Day 1)
  2. Send assessment (Day 2)
  3. Review results (Day 5)
  4. Schedule interview (Day 7)
  5. Send offer (Day 10)

Apply to applicant:
- Auto-creates all activities
- Sets deadlines
- Assigns to recruiter
```

**3. Track Activities**
```
My Dashboard → Planned Activities

Shows:
- Today's activities
- Overdue activities
- Upcoming activities
- Activity details

Actions:
- Mark done
- Reschedule
- Cancel
- Edit notes
```

#### Meeting Integration

**1. Schedule Meeting**
```
Applicant → Schedule Meeting

Creates calendar event:
✓ Meeting subject
✓ Date/time
✓ Duration
✓ Location/video link
✓ Attendees (interviewers)
✓ Applicant invited
✓ Description/agenda
✓ Attachments shared

Sends:
✓ Calendar invitations
✓ Email notifications
✓ Reminder notifications
```

**2. Meeting Types**
```
Phone Screen:
- Duration: 30 min
- Attendees: Recruiter
- Format: Phone/video

First Interview:
- Duration: 1 hour
- Attendees: Hiring manager, recruiter
- Format: Video/in-person

Second Interview:
- Duration: 2 hours
- Attendees: Team members, manager
- Format: In-person

Final Interview:
- Duration: 1 hour
- Attendees: Senior leadership
- Format: In-person
```

**3. Meeting Follow-up**
```
After meeting:
1. Log notes in chatter
2. Update applicant stage
3. Schedule next steps
4. Send follow-up email
5. Create activity (if needed)
```

### Website Integration

**Prerequisites:**
- website_hr_recruitment module installed
- Website configured
- Company settings updated

#### Publishing Jobs

**1. Publish Job to Website**
```
Jobs → Select Job → Edit

Website Tab:
✓ Website Published: Check
- Website Description: SEO description
- Job Details: Process/benefits info

Save → Go to Website

Result:
✓ Job visible on career page
✓ SEO-friendly URL created
✓ Application form enabled
✓ Social sharing enabled
```

**2. Job Description**
```
Jobs → Description Tab

Rich text editor:
- Job summary
- Responsibilities
- Requirements
- Qualifications
- Benefits
- Company info
- Application instructions

Formatting:
- Headers
- Bold/italic
- Bullet lists
- Links
- Images (company logo, office photos)
```

**3. SEO Optimization**
```
Website Description field:
- 150-160 characters
- Include job title
- Include location
- Include key requirements
- Include company name

Example:
"Senior Software Engineer needed in Mumbai. Join our 
innovative tech team. Python, Django, 5+ years exp. 
Apply now at [Company]."
```

**4. URL Customization**
```
Auto-generated URL:
/jobs/detail/senior-software-engineer-15

Includes:
- Job slug (from title)
- Job ID
- SEO-friendly format
```

#### Career Page

**Access Career Page**
```
Main website → Careers
OR
Direct URL: yourcompany.com/jobs
```

**Public Job Board Features**

**1. Job Listing**
```
Display:
- Job title
- Department
- Location
- Remote option
- Posted date
- Brief description

Sorting:
- Newest first (default)
- Department
- Location
```

**2. Search & Filters**
```
Search bar:
- Full-text search
- Job title search
- Description search

Filters:
- Department: Engineering, Sales, Marketing, etc.
- Office Location: Mumbai, Delhi, Bangalore, etc.
- Country: India, USA, etc.
- Employment Type: Full-time, Part-time, Contract
- Remote Work: Yes/No
```

**3. Job Details Page**
```
yourcompany.com/jobs/detail/job-title-id

Displays:
- Full job description
- Requirements
- Qualifications
- Benefits
- Company info
- Application form

Features:
- Apply button (scrolls to form)
- Social sharing (LinkedIn, Facebook, Twitter)
- Print job description
- Related jobs
```

#### Online Application Process

**1. Application Form**
```
Public Form Fields:
┌─────────────────────────────────┐
│ Your Name *                     │
│ [                    ]          │
│                                 │
│ Email Address *                 │
│ [                    ]          │
│                                 │
│ Phone Number *                  │
│ [                    ]          │
│                                 │
│ LinkedIn Profile                │
│ [                    ]          │
│                                 │
│ Upload Your Resume *            │
│ [Choose File] No file chosen    │
│                                 │
│ Cover Letter / Message          │
│ [                              ]│
│ [                              ]│
│ [                              ]│
│                                 │
│ [ Submit Application ]          │
└─────────────────────────────────┘

* Required fields
```

**2. Form Validation**
```
Client-side:
- Required field validation
- Email format validation
- Phone format validation
- File type validation (PDF, DOC, DOCX)
- File size limit (10 MB)

Server-side:
- Duplicate application check
- Sanitize inputs
- Validate contact info
- Check job is open
```

**3. Application Submission**
```
On Submit:

Backend Process:
1. Validate form data
2. Check for duplicate applications
3. Create applicant record
4. Assign to job position
5. Set initial stage (New)
6. Attach resume
7. Create partner (if needed)
8. Send confirmation email
9. Track UTM parameters
10. Log in chatter

User sees:
"Thank you! Your application has been received. 
We will review it and contact you soon."
```

**4. Duplicate Detection**
```
Checks for existing applications by:
- Same email + same job
- Same phone + same job
- Same LinkedIn + same job

If duplicate found:
- Option 1: Prevent submission
- Option 2: Allow submit with warning
- Option 3: Link to existing application
```

#### UTM Tracking

**1. Campaign URLs**
```
Job Sources → Create Source

Auto-generated URL:
yourcompany.com/jobs/detail/job-title-15
?utm_campaign=linkedin_jobs
&utm_medium=social
&utm_source=linkedin

Tracks:
- Where candidate came from
- Which campaign
- What medium (social, email, referral)
```

**2. Source Analytics**
```
Applications → Group by Source

Report shows:
- Total applications per source
- Conversion rate per source
- Quality of applications
- Cost per hire (if cost tracked)
- Best performing sources
```

**3. Campaign ROI**
```
UTM Campaigns → Analytics

Metrics:
- Applications received
- Qualified candidates
- Interviews conducted
- Hires made
- Time to hire
- Cost per hire
- ROI calculation
```

#### Website Customization

**1. Career Page Layout**
```
Website Builder:
- Customize header
- Add company info section
- Feature benefits
- Show office photos
- Add testimonials
- Customize colors/branding
```

**2. Application Form Customization**
```
Settings → Recruitment:
- Add custom questions
- Enable/disable fields
- Require additional documents
- Add disclaimers
- Privacy policy
```

**3. Multi-Website Support**
```
For companies with multiple brands:
- Publish job to specific website
- Different branding per site
- Separate application flows
- Separate contact emails
```

---

## Technical Reference

### Data Models

#### hr.applicant

```python
class Applicant(models.Model):
    _name = 'hr.applicant'
    _description = 'Applicant'
    _order = 'priority desc, id desc'
    _inherit = ['mail.thread.cc', 
                'mail.thread.phone', 
                'mail.activity.mixin', 
                'utm.mixin']
    
    # Core Fields
    sequence = fields.Integer()
    active = fields.Boolean(default=True)
    partner_id = fields.Many2one('res.partner')
    partner_name = fields.Char()
    email_from = fields.Char(index='trigram')
    partner_phone = fields.Char()
    linkedin_profile = fields.Char()
    
    # Job & Employment
    job_id = fields.Many2one('hr.job', required=True)
    department_id = fields.Many2one('hr.department')
    company_id = fields.Many2one('res.company')
    user_id = fields.Many2one('res.users')
    employee_id = fields.Many2one('hr.employee')
    interviewer_ids = fields.Many2many('res.users')
    
    # Stage & Status
    stage_id = fields.Many2one('hr.recruitment.stage')
    last_stage_id = fields.Many2one('hr.recruitment.stage')
    kanban_state = fields.Selection([...])
    application_status = fields.Selection([
        ('ongoing', 'Ongoing'),
        ('hired', 'Hired'),
        ('refused', 'Refused'),
        ('archived', 'Archived')
    ])
    refuse_reason_id = fields.Many2one('hr.applicant.refuse.reason')
    
    # Salary
    salary_proposed = fields.Float()
    salary_expected = fields.Float()
    salary_proposed_extra = fields.Text()
    salary_expected_extra = fields.Text()
    
    # Tracking
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Good'),
        ('2', 'Very Good'),
        ('3', 'Excellent')
    ], default='0')
    probability = fields.Float()
    
    # Dates
    availability = fields.Date()
    date_open = fields.Datetime(readonly=True)
    date_closed = fields.Datetime(readonly=True)
    date_last_stage_update = fields.Datetime()
    
    # Talent Pool
    talent_pool_ids = fields.Many2many('hr.talent.pool')
    is_pool_applicant = fields.Boolean()
    
    # Other
    type_id = fields.Many2one('hr.recruitment.degree')
    categ_ids = fields.Many2many('hr.applicant.category')
    attachment_ids = fields.One2many('ir.attachment', ...)
    meeting_ids = fields.Many2many('calendar.event')
    applicant_properties = fields.Properties()
```

#### hr.job

```python
class Job(models.Model):
    _name = 'hr.job'
    _inherit = ['hr.job', 'website.published.multi.mixin']
    
    # Recruitment Fields
    application_ids = fields.One2many('hr.applicant')
    application_count = fields.Integer(compute='...')
    new_application_count = fields.Integer(compute='...')
    applicant_hired = fields.Integer(compute='...')
    
    # Email & Sources
    alias_id = fields.Many2one('mail.alias')
    job_source_ids = fields.One2many('hr.recruitment.source')
    
    # Interviewers
    interviewer_ids = fields.Many2many('res.users')
    extended_interviewer_ids = fields.Many2many(compute='...')
    
    # Requirements
    expected_degree = fields.Many2one('hr.recruitment.degree')
    industry_id = fields.Many2one('res.partner.industry')
    
    # Properties
    job_properties = fields.Properties()
    applicant_properties_definition = fields.PropertiesDefinition()
    
    # Website
    description = fields.Html()
    website_description = fields.Text()
    job_details = fields.Html()
    published_date = fields.Datetime()
```

#### hr.recruitment.stage

```python
class Stage(models.Model):
    _name = 'hr.recruitment.stage'
    _description = 'Recruitment Stage'
    _order = 'sequence'
    
    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    job_ids = fields.Many2many('hr.job')
    requirements = fields.Text()
    template_id = fields.Many2one('mail.template')
    fold = fields.Boolean()
    hired_stage = fields.Boolean()
    rotting_threshold_days = fields.Integer(default=7)
    
    # Kanban Legends
    legend_blocked = fields.Char(default='Blocked')
    legend_done = fields.Char(default='Ready for Next Stage')
    legend_normal = fields.Char(default='In Progress')
    legend_waiting = fields.Char(default='Waiting')
```

#### hr.talent.pool

```python
class TalentPool(models.Model):
    _name = 'hr.talent.pool'
    _description = 'Talent Pool'
    
    active = fields.Boolean(default=True)
    name = fields.Char(required=True)
    company_id = fields.Many2one('res.company')
    pool_manager = fields.Many2one('res.users')
    talent_ids = fields.One2many('hr.applicant')
    no_of_talents = fields.Integer(compute='...')
    description = fields.Text()
    color = fields.Integer()
    categ_ids = fields.Many2many('hr.applicant.category')
```

### Key Methods

#### hr.applicant

```python
# Create Employee
def create_employee_from_applicant(self):
    """Convert applicant to employee"""
    employee = self.env['hr.employee'].create({
        'name': self.partner_name,
        'job_id': self.job_id.id,
        'department_id': self.department_id.id,
        # ... more fields
    })
    
    # Copy attachments
    self.attachment_ids.copy({'res_model': 'hr.employee', 
                              'res_id': employee.id})
    
    # Mark as hired
    self.write({
        'employee_id': employee.id,
        'application_status': 'hired',
        'active': False
    })
    
    return employee

# Archive
def archive_applicant(self):
    """Archive applicant"""
    self.write({
        'active': False,
        'application_status': 'archived'
    })

# Refuse
def refuse_applicant(self, refuse_reason_id):
    """Refuse applicant with reason"""
    self.write({
        'refuse_reason_id': refuse_reason_id,
        'application_status': 'refused',
        'refuse_date': fields.Datetime.now(),
        'active': False
    })

# Reset
def reset_applicant(self):
    """Reset to first stage"""
    first_stage = self.env['hr.recruitment.stage'].search(
        [], order='sequence', limit=1
    )
    self.write({
        'stage_id': first_stage.id,
        'refuse_reason_id': False,
        'refuse_date': False,
        'application_status': 'ongoing',
        'kanban_state': 'normal'
    })

# Stage Change
def write(self, vals):
    """Override to trigger stage actions"""
    if 'stage_id' in vals:
        # Update last stage
        vals['last_stage_id'] = self.stage_id.id
        vals['date_last_stage_update'] = fields.Datetime.now()
        
        # Send stage email if configured
        stage = self.env['hr.recruitment.stage'].browse(vals['stage_id'])
        if stage.template_id:
            stage.template_id.send_mail(self.id)
    
    return super().write(vals)
```

#### hr.job

```python
# Create Recruitment Source
def action_create_source(self):
    """Create UTM source for job"""
    source = self.env['hr.recruitment.source'].create({
        'job_id': self.id,
        'email': self.alias_name,
        'campaign_id': self.campaign_id.id,
        'medium_id': self.medium_id.id,
    })
    return source

# Get Job URL
def get_job_url(self):
    """Get website URL for job"""
    return f'/jobs/detail/{slugify(self.name)}-{self.id}'
```

### Email Gateway

**Incoming Mail Processing**

```python
# Mail alias configuration
{
    'alias_name': 'senior-software-engineer-15',
    'alias_model_id': 'hr.applicant',
    'alias_defaults': {
        'job_id': 15,
        'stage_id': 1,  # New stage
    }
}

# Processing flow
Email arrives → Mail Gateway
    ↓
Extract info:
- From: email, name, phone
- Subject: use as application title
- Body: store in description
- Attachments: link to applicant
    ↓
Create/update applicant:
- Check for duplicate (email + job)
- Create new or update existing
- Assign to job
- Set initial stage
- Create/link partner
    ↓
Notify:
- Chatter message
- Activity created
- Recruiter notified
```

### Automated Actions

**Stage Email Automation**

```python
# Trigger: Stage change
# Model: hr.applicant
# Condition: stage_id.template_id exists

Action:
- Send email using stage template
- Log in chatter
- Update sent counter
```

**Rotting Applicant Detection**

```python
# Scheduled action (daily)
# Find rotting applicants

applicants = env['hr.applicant'].search([
    ('active', '=', True),
    ('application_status', '=', 'ongoing'),
    ('date_last_stage_update', '<', 
     fields.Datetime.now() - timedelta(days=threshold))
])

# Create activity for recruiter
for applicant in applicants:
    applicant.activity_schedule(
        act_type_id=follow_up_activity,
        summary=f'Follow up on rotting applicant: {applicant.partner_name}',
        user_id=applicant.user_id.id
    )
```

### API Endpoints (Future)

```python
# REST API endpoints (if implemented)

# List jobs
GET /api/v1/jobs
Response: {jobs: [...], total: 50}

# Job details
GET /api/v1/jobs/<job_id>
Response: {id, name, description, requirements, ...}

# Submit application
POST /api/v1/jobs/<job_id>/apply
Payload: {name, email, phone, resume, ...}
Response: {applicant_id, status: 'submitted'}

# Application status
GET /api/v1/applications/<token>
Response: {status, stage, last_update, ...}
```

---

## Workflows

### Standard Recruitment Workflow

```
Job Position Created
    ↓
Configure Requirements
- Set required skills
- Define expected degree
- Add interviewers
- Create email alias
- Set up recruitment sources
    ↓
Publish Job
- Website
- Job boards (LinkedIn, Indeed, etc.)
- Social media
- Referrals
    ↓
Receive Applications
- Email gateway
- Website form
- Manual entry
- Import
    ↓
Stage: New
- Auto-assignment to job
- Initial stage
- Confirmation email sent
    ↓
Stage: Qualification
- Resume review
- Skills matching
- Initial screening
- Schedule phone screen
    ↓
Stage: First Interview
- Phone/video interview
- Basic evaluation
- Assess fit
- Log notes
    ↓
Stage: Second Interview
- In-person/technical interview
- Team interview
- Assessment/test
- Reference checks
    ↓
Stage: Contract Proposal
- Prepare offer
- Salary negotiation
- Send offer letter
- Await decision
    ↓
Stage: Contract Signed (Hired)
- Contract signed
- Create employee record
- Copy data
- Welcome email
- Mark as hired
    ↓
Onboarding
- HR processes
- IT setup
- Training
```

### Talent Pool Workflow

```
Quality Candidate (Not Hired)
    ↓
Add to Talent Pool
- Select appropriate pool
- Add relevant tags
- Log reason
    ↓
Maintain in Pool
- Keep contact updated
- Track in newsletter
- Engage periodically
    ↓
New Position Opens
    ↓
Search Talent Pool
- Filter by skills
- Filter by tags
- Check availability
    ↓
Apply to New Job
- Create application
- Start at advanced stage
- Fast-track process
    ↓
Hire or Return to Pool
```

### Website Application Workflow

```
Candidate Visits Career Page
    ↓
Browse Jobs
- Search/filter
- Read descriptions
- Compare positions
    ↓
Select Job
    ↓
Read Full Description
- Requirements
- Benefits
- Company info
    ↓
Click Apply
    ↓
Fill Application Form
- Name, email, phone
- LinkedIn profile
- Upload resume
- Cover letter
    ↓
Submit Application
    ↓
System Processing
- Validate data
- Check duplicates
- Create applicant
- Assign to job
- Set initial stage
- Attach documents
- Track UTM
    ↓
Confirmation
- Thank you message
- Confirmation email
    ↓
Recruiter Notified
- New application activity
- Email notification
    ↓
Standard Recruitment Process
```

### Skills Matching Workflow

```
Define Job Requirements
- Required skills list
- Skill levels
- Expected degree
    ↓
Applicant Applies
    ↓
Record Applicant Skills
- From resume (manual)
- From assessment
- From LinkedIn
    ↓
Calculate Match Score
- Compare skills: required vs actual
- Check skill levels
- Include degree
- Weighted scoring
    ↓
Match Score: 0-100%
    ↓
Filter & Rank
- Filter minimum score
- Rank by score
- Prioritize review
    ↓
Focus on Top Matches
- Interview best matches first
- Fast-track high scorers
    ↓
Hire Decision
    ↓
Transfer Skills to Employee
- Copy all skills
- Preserve levels
- Link to employee
```

### Interview Assessment Workflow

```
Create Interview Form
- Survey module
- Add questions
- Set scoring
    ↓
Link to Job Position
    ↓
Applicant Progresses
- Reaches assessment stage
    ↓
Send Interview Form
- Email invitation
- Unique link
- Set deadline
    ↓
Applicant Completes
- Online form
- Submit responses
    ↓
System Notifies
- Completion notification
- Chatter message
- Activity created
    ↓
Recruiter Reviews
- View responses
- Check score
- Evaluate answers
    ↓
Decision
- Advance or refuse
- Log evaluation
    ↓
Next Stage
```

---

## Best Practices

### Job Position Setup

**1. Clear Job Descriptions**
```
✓ DO:
- Write detailed, accurate descriptions
- List specific requirements
- Include must-haves vs nice-to-haves
- Mention company culture/benefits
- Use inclusive language
- Optimize for SEO (if publishing to website)

✗ DON'T:
- Copy generic descriptions
- Be vague about requirements
- Use discriminatory language
- Overpromise/mislead
- Forget to update when role changes
```

**2. Skill Requirements**
```
✓ DO:
- List only essential skills
- Specify required proficiency levels
- Distinguish must-haves from preferences
- Use standard skill names
- Include certifications if needed

✗ DON'T:
- List every possible skill
- Require expert level for entry positions
- Use proprietary/non-standard terms
- Add skills not actually needed
```

**3. Email Aliases**
```
✓ DO:
- Use descriptive alias names
- Keep aliases active
- Monitor for spam
- Test email routing
- Document for team

✗ DON'T:
- Use confusing names
- Share aliases across jobs
- Forget to disable when filled
```

### Application Management

**1. Response Time**
```
Best Practice: Respond within 24-48 hours

Auto-acknowledgment:
- Send confirmation immediately
- Set expectations on timeline
- Provide status check method

Regular updates:
- Keep applicants informed
- Explain delays if any
- Be respectful of their time
```

**2. Communication**
```
✓ DO:
- Be professional and courteous
- Personalize communications
- Be clear about next steps
- Respond to all applicants
- Provide feedback when possible

✗ DON'T:
- Leave applicants hanging
- Send generic, impersonal emails
- Make promises you can't keep
- Ghost candidates
```

**3. Organization**
```
✓ DO:
- Use tags consistently
- Add notes after every interaction
- Keep documents organized
- Update stages promptly
- Log all communications

✗ DON'T:
- Skip documentation
- Let applicants rot in stages
- Forget to update status
```

### Pipeline Management

**1. Stage Transitions**
```
Best Practices:
- Move applicants promptly
- Don't skip stages
- Log reason for stage changes
- Set automatic email templates
- Monitor stage duration

Red Flags:
- Applicants stuck >14 days in one stage
- Skipping stages
- No notes on transitions
```

**2. Interviewing**
```
✓ DO:
- Schedule promptly
- Prepare interviewers
- Use structured interviews
- Take detailed notes
- Evaluate objectively
- Provide feedback

✗ DON'T:
- Wing it without preparation
- Ask illegal questions
- Evaluate based on bias
- Take too long to decide
```

**3. Refusals**
```
✓ DO:
- Refuse promptly
- Provide reason (internal)
- Send polite email
- Add to talent pool if qualified
- Document decision

✗ DON'T:
- Ghost candidates
- Be rude or dismissive
- Provide too much detail (legal risk)
```

### Talent Pool

**1. Pool Organization**
```
Create Specific Pools:
- By role type (Engineers, Sales, etc.)
- By source (Campus, Referrals, etc.)
- By period (Q1 2026, etc.)
- By specialty (Frontend, Backend, etc.)

Tag Effectively:
- Skills
- Location preferences
- Availability
- Referrer
- Interest level
```

**2. Pool Maintenance**
```
✓ DO:
- Keep contact info updated
- Engage periodically (newsletters)
- Re-evaluate skills
- Remove unresponsive contacts
- Track engagement

✗ DON'T:
- Let pool go stale
- Add everyone indiscriminately
- Spam pool members
- Forget to track consent
```

### Compliance & Privacy

**1. Data Protection**
```
GDPR/Privacy Considerations:
- Get consent to store data
- Document retention policy
- Allow applicants to request deletion
- Secure sensitive data
- Limit access to need-to-know
- Anonymize for reporting
```

**2. Equal Opportunity**
```
✓ DO:
- Use objective criteria
- Standardize interviews
- Document decisions
- Train on bias
- Track diversity metrics

✗ DON'T:
- Discriminate based on protected classes
- Ask illegal questions
- Make assumptions
- Use subjective criteria only
```

**3. Documentation**
```
Document:
- All interview notes
- Refusal reasons
- Stage progression
- Communications
- Decision rationale

Keep for:
- Legal compliance
- Audit trail
- Process improvement
- Disputes resolution
```

### Performance Optimization

**1. Source Tracking**
```
Track Effectiveness:
- Applications per source
- Quality per source
- Cost per hire per source
- Time to hire per source
- Conversion rate per source

Optimize:
- Invest in best sources
- Cut poor performers
- Test new sources
- A/B test messaging
```

**2. Process Metrics**
```
Monitor:
- Time to hire (target: <30 days)
- Cost per hire
- Offer acceptance rate (target: >80%)
- Quality of hire (90-day performance)
- Candidate satisfaction
- Diversity metrics

Improve:
- Streamline bottlenecks
- Reduce stage duration
- Improve communication
- Enhance candidate experience
```

### Team Collaboration

**1. Role Clarity**
```
Define:
- Who sources candidates
- Who screens initially
- Who conducts interviews
- Who makes final decision
- Who sends offers
- Who handles admin

Document in:
- Stage requirements
- Activity plans
- Team procedures
```

**2. Communication**
```
✓ DO:
- Use chatter for all updates
- Tag relevant team members
- Schedule debriefs after interviews
- Share feedback promptly
- Escalate issues quickly

✗ DON'T:
- Use external communication
- Keep decisions to yourself
- Delay feedback
- Skip team alignment
```

---

## FAQ

### General Questions

**Q: What's the difference between hr_recruitment and other recruitment modules?**

A: The Odoo recruitment system is modular:
- **hr_recruitment** - Core ATS functionality (job posting, applicant tracking, pipeline)
- **hr_recruitment_skills** - Adds skills matching and scoring
- **hr_recruitment_survey** - Adds interview assessments/tests
- **hr_recruitment_sms** - Adds SMS communication
- **website_hr_recruitment** - Adds website job board and online applications

Install only what you need.

**Q: Can I customize the recruitment stages?**

A: Yes, completely customizable:
- Add/remove/rename stages
- Change sequence
- Set per-job stages
- Configure email templates per stage
- Set hiring stage
- Configure rotting thresholds

**Q: How do I handle multiple openings for the same role?**

A: Create one job position with "No. of Recruitment = X". Track all applicants under that job. When filling positions, create employees one by one.

**Q: Can applicants apply to multiple jobs?**

A: Yes, they can have separate application records for each job. System detects if same email/phone applies to different jobs.

### Application Management

**Q: How do I prevent duplicate applications?**

A: System automatically detects duplicates by:
- Same email + same job
- Same phone + same job
- Same LinkedIn + same job

Use "Find Duplicates" feature to batch refuse/link them.

**Q: Can I import existing applications?**

A: Yes:
1. Go to Applications
2. Favorites → Import Records
3. Upload CSV/Excel
4. Map fields
5. Validate and import

**Q: What happens when I create an employee from applicant?**

A: System:
1. Creates employee record
2. Copies basic info (name, email, phone, job, department)
3. Transfers documents/attachments
4. Copies skills (if skills module installed)
5. Links employee to applicant
6. Marks applicant as hired
7. Archives applicant record

**Q: Can I reopen a refused/archived applicant?**

A: Yes:
1. Go to Applications
2. Filters → Archived
3. Select applicant
4. Action → Unarchive
5. Or use "Reset Applicant" to return to first stage

### Communication

**Q: How do email aliases work?**

A: Each job can have a dedicated email address:
- Format: job-slug-{id}@yourdomain.com
- Example: software-engineer-15@company.com
- Emails sent to this address automatically create applicants assigned to that job
- Requires email gateway configured

**Q: Can I send bulk emails to applicants?**

A: Yes:
1. Select multiple applicants
2. Action → Send Email
3. Choose template
4. System personalizes for each applicant
5. Send immediately or schedule

**Q: How do I track email opens/clicks?**

A: Email statistics tracked in Mailings app (if installed). Each email logged in chatter with delivery status.

**Q: Can I schedule emails?**

A: Yes, use the "Schedule" option in email composer to send at a specific date/time.

### Talent Pool

**Q: What's the difference between an applicant and a talent?**

A: 
- **Applicant**: Application for a specific job
- **Talent**: Person in talent pool for future opportunities
- A person can be both (apply to current job + added to pool)
- Talents can be converted to applicants for new jobs

**Q: How do I add someone directly to talent pool without a job application?**

A: Create an applicant manually, apply to a generic "Talent Pool" job, then add to pool. Or use the pool's "Add Applicants" wizard.

**Q: Can one person be in multiple talent pools?**

A: Yes, talents can be in multiple pools with different tags.

### Skills Matching

**Q: How is the matching score calculated?**

A: 
```
Base Score = (Matching Skills / Total Required Skills) × 100
Degree Bonus = +10-20% if meets/exceeds degree requirement
Final Score = Base Score + Degree Bonus (max 100%)
```

**Q: Does it consider skill levels?**

A: Yes, applicant must meet or exceed required skill level. Having Python at Expert level when Intermediate required is a match. Having Intermediate when Expert required is not a full match.

**Q: Can I filter applicants by skills?**

A: Yes:
1. Applications → Filters → Add Custom Filter
2. Field: Skill IDs
3. Operator: Contains
4. Value: Select skill
5. Apply

Or use matching score filter.

### Website Integration

**Q: How do I publish jobs to my website?**

A: 
1. Install website_hr_recruitment module
2. Edit job
3. Check "Website Published"
4. Add website description
5. Save
6. Job appears on yoursite.com/jobs

**Q: Can I customize the career page?**

A: Yes, use website builder:
1. Go to website
2. Navigate to /jobs
3. Click "Edit"
4. Customize layout, colors, content
5. Save

**Q: How do I track which jobs get the most views?**

A: Enable website analytics to track page views per job URL.

**Q: Can I have multiple career sites?**

A: Yes, with multi-website module. Publish each job to specific website(s).

### Reporting & Analytics

**Q: What reports are available?**

A: Standard reports:
- Applications by stage
- Applications by source
- Time to hire
- Hiring funnel
- Source effectiveness

Create custom reports using pivot/graph views.

**Q: How do I track cost per hire?**

A: Not built-in. Track manually by:
1. Adding cost field (customization)
2. Or tracking in UTM campaigns
3. Or using separate accounting system

**Q: Can I export data?**

A: Yes:
1. Select records (or select all)
2. Action → Export
3. Choose fields
4. Download CSV/Excel

### Technical

**Q: Can I add custom fields?**

A: Yes:
1. Enable developer mode
2. Settings → Technical → Database Structure → Models
3. Find hr.applicant
4. Add fields
5. Add to views

Or use Properties for dynamic fields per job.

**Q: Can I create automation rules?**

A: Yes:
1. Settings → Technical → Automation → Automated Actions
2. Model: Applicant
3. Trigger: On creation, update, etc.
4. Conditions: Filter conditions
5. Actions: Send email, update field, etc.

**Q: Is there an API?**

A: Use Odoo's standard XML-RPC or JSON-RPC API. All models accessible programmatically.

**Q: Can I integrate with external job boards?**

A: Yes, via:
1. Email gateway (Indeed, LinkedIn send applications via email)
2. API integration (custom development)
3. Zapier/integromat connectors
4. Custom modules

**Q: How do I backup recruitment data?**

A: Use Odoo's backup feature or export data regularly. Database backups include all recruitment records.

---

## Support & Resources

### Documentation
- Official Odoo Docs: https://www.odoo.com/documentation/19.0/applications/hr/recruitment.html
- Community Forum: https://www.odoo.com/forum
- GitHub: https://github.com/odoo/odoo (addons/hr_recruitment)

### Training
- Odoo eLearning: https://www.odoo.com/slides
- Official Training: https://www.odoo.com/training
- YouTube Tutorials: Search "Odoo Recruitment"

### Support
- Community Edition: Forum support
- Enterprise Edition: Official support tickets
- Partners: Certified Odoo partners

### Customization
- Developer Documentation: https://www.odoo.com/documentation/19.0/developer.html
- App Store: https://apps.odoo.com (search "recruitment")
- Hire Developer: Odoo partners or freelancers

---

## Version History

**Odoo 19.0** (Current)
- Enhanced properties system
- Improved talent pools
- Better skills matching
- Modern UI updates

**Odoo 18.0**
- Talent pool management
- Properties system introduced
- Enhanced website integration

**Odoo 17.0**
- Skills-based recruitment
- Survey integration
- Improved email templates

**Previous Versions**
- Core recruitment pipeline
- Email gateway
- Basic website integration
- UTM tracking

---

## Conclusion

The Odoo HR Recruitment system provides a comprehensive solution for managing the entire hiring lifecycle. From job posting to employee onboarding, the system streamlines recruitment processes, improves candidate experience, and provides valuable analytics for data-driven hiring decisions.

**Key Takeaways:**

✅ **Modular System** - Install only what you need  
✅ **Customizable Pipeline** - Adapt to your processes  
✅ **Multi-Channel Sourcing** - Reach candidates everywhere  
✅ **Skills-Based Matching** - Find the best candidates  
✅ **Talent Pool** - Build pipeline for future needs  
✅ **Professional Communication** - Email, SMS, surveys  
✅ **Website Integration** - Modern career site  
✅ **Data-Driven** - Analytics and reporting  

**Next Steps:**

1. Install the modules you need
2. Configure stages and settings
3. Create your first job position
4. Start receiving applications
5. Build your talent pool
6. Continuously improve your process

Happy Recruiting! 🎯

---

**Document Version:** 1.0  
**Last Updated:** February 12, 2026  
**Author:** ClearDeals Tech Team
**Module Versions:** Odoo 19.0 Community/Enterprise  

---

*For questions or feedback on this documentation, contact your system administrator or HR team.*

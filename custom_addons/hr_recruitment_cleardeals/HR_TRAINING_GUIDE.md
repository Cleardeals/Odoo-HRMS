# HR Recruitment System - Training Guide for HR Teams

## Welcome! 👋

This guide will help you master the Odoo Recruitment system and hire the best talent efficiently. No technical jargon - just practical, easy-to-follow instructions for your daily work.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Understanding Key Concepts](#understanding-key-concepts)
3. [Your First Week Setup](#your-first-week-setup)
4. [Daily Tasks & Tutorials](#daily-tasks--tutorials)
5. [Advanced Features](#advanced-features)
6. [Optimization Tips by Role](#optimization-tips-by-role)
7. [Common Scenarios](#common-scenarios)
8. [Quick Reference](#quick-reference)
9. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Logging In

1. Open your web browser
2. Go to your company's Odoo URL (e.g., `yourcompany.odoo.com`)
3. Enter your username and password
4. Click **Log In**

### Finding the Recruitment App

Once logged in:
1. Look at the top menu bar
2. Click on **Recruitment** (purple icon with a person)
3. You'll see the main recruitment dashboard

**Main Menu Items:**
- **Applications** - All candidate applications
- **Jobs** - Open positions you're hiring for
- **Talent Pools** - Your database of potential candidates
- **Configuration** - Settings and customization

---

## Understanding Key Concepts

Before we dive in, let's understand what each term means in simple language.

### 📋 What is an "Applicant"?

**Simple Definition:** A person who has applied for a job at your company.

**Think of it as:** A digital folder containing everything about one candidate's application - their resume, contact info, interview notes, emails you've sent them, etc.

**Example:** Sarah applies for "Marketing Manager" → System creates an applicant record for Sarah.

---

### 💼 What is a "Job Position"?

**Simple Definition:** A role you're trying to fill in your company.

**Think of it as:** The job posting with all its details - title, description, requirements, who's hiring for it, how many people you need, etc.

**Example:** "Senior Software Engineer" position in Engineering department, need to hire 2 people.

---

### 🎯 What is a "Stage"?

**Simple Definition:** A step in your hiring process.

**Think of it as:** Like a checklist where candidates move from one step to the next. Each stage represents where the candidate is in the hiring journey.

**Default Stages:**
1. **New** - Just received the application
2. **Qualification** - Reviewing if they meet basic requirements
3. **First Interview** - Phone/video screening call
4. **Second Interview** - In-person or technical interview
5. **Contract Proposal** - Offering them the job
6. **Contract Signed** - They accepted! Time to hire them.

**Example:** John's application starts at "New" → You review his resume and move him to "Qualification" → He passes, so you move him to "First Interview" → and so on.

---

### 🏊 What is a "Talent Pool"?

**Simple Definition:** A collection of good candidates you want to remember for future positions.

**Think of it as:** Like saving contacts on your phone. These are people who didn't get hired this time, but were impressive enough to keep in your database for future opportunities.

**Why it's useful:** Instead of starting from scratch every time, you have a ready list of pre-screened candidates.

**Example:** You interview 5 great candidates for 1 position. You hire 1, but add the other 4 to your "Marketing Professionals" talent pool. Next time you have a marketing opening, you contact them first.

---

### 🎓 What are "Skills"?

**Simple Definition:** Specific abilities or knowledge areas that candidates have (or jobs require).

**Think of it as:** Labels that describe what someone can do - like "Python Programming," "Sales," "Public Speaking," etc.

**How it helps:** The system can automatically match candidates who have the skills you need for a job.

**Example:** 
- Job requires: Python (Expert), Project Management (Intermediate)
- Candidate has: Python (Expert) ✓, Project Management (Beginner) ✗
- Match score: 50%

---

### 📊 What is "Kanban View"?

**Simple Definition:** A visual board showing all your candidates organized by stages.

**Think of it as:** Like sticky notes on a whiteboard. Each candidate is a card, and stages are columns. You drag cards from column to column as they progress.

**Why it's great:** You can see your entire hiring pipeline at a glance.

**Visual Example:**
```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│    New      │  │ First Int.  │  │   Offer     │
├─────────────┤  ├─────────────┤  ├─────────────┤
│ Sarah M.    │  │ John D.     │  │ Amy L.      │
│ Mike T.     │  │ Lisa K.     │  │             │
│ Emma R.     │  │             │  │             │
└─────────────┘  └─────────────┘  └─────────────┘
```

---

### 📧 What is an "Email Alias"?

**Simple Definition:** A special email address for a specific job that automatically creates applicant records.

**Think of it as:** A magic email box. When someone sends their resume to this email, the system automatically creates their application, assigns it to the job, and notifies you.

**Example:** 
- Job: Senior Developer
- Email Alias: `senior-developer@yourcompany.com`
- Someone emails their resume → System creates applicant automatically
- You get notified → Start reviewing

---

### 🏷️ What are "Tags"?

**Simple Definition:** Labels you can attach to candidates to categorize them.

**Think of it as:** Like hashtags on social media. They help you organize and find candidates quickly.

**Example Tags:**
- "Referral" - Someone referred them
- "Remote Worker" - Open to remote work
- "Relocatable" - Willing to move cities
- "Premium Candidate" - Top quality applicant

---

### 🎯 What is "UTM Tracking"?

**Simple Definition:** A way to track where your candidates are coming from.

**Think of it as:** Like asking "How did you hear about us?" but automatic. It tracks if they came from LinkedIn, Indeed, your website, a referral, etc.

**Why it matters:** You can see which job posting sites or ads bring the best candidates, so you know where to invest your recruitment budget.

**Example:**
- Posted job on LinkedIn: 50 applications, 5 hired
- Posted same job on Indeed: 100 applications, 2 hired
- **Result:** LinkedIn brings better quality despite fewer applicants

---

## Your First Week Setup

Follow these steps in your first week to set up the system properly.

### Day 1: Configure Your Settings

**⏱️ Time needed:** 30 minutes

#### Step 1: Set Up Recruitment Stages

1. Click **Recruitment** in the top menu
2. Click **Configuration** → **Stages**
3. You'll see default stages (New, Qualification, etc.)

**Review each stage:**
- Click on a stage name to open it
- Check if the name makes sense for your company
- You can rename them if needed (e.g., "Phone Screen" instead of "First Interview")

**Example Customization:**
```
Your tech hiring process might be:
1. New Application
2. Resume Review
3. Phone Screen
4. Technical Test
5. Team Interview
6. Manager Interview
7. Offer
8. Hired

Your sales hiring might be:
1. New Application
2. Initial Screening
3. Sales Assessment
4. Role-Play Interview
5. Offer
6. Hired
```

**To add a new stage:**
1. Click **Create**
2. Enter **Stage Name**
3. Set **Sequence** (determines order - lower numbers come first)
4. Save

**To reorder stages:**
1. Drag and drop them in the list view

**💡 Tip:** Keep it simple! 5-7 stages is ideal. Too many stages slow down your process.

---

#### Step 2: Set Up Refusal Reasons

**Why this matters:** When you reject candidates, you'll track why. This helps you improve your job descriptions and understand common rejection reasons.

1. Go to **Configuration** → **Refuse Reasons**
2. Review the default reasons:
   - Does not fit job requirements
   - Refused by applicant: job fit
   - Refused by applicant: salary
   - Job already fulfilled
   - Duplicate application
   - Spam

**To add a custom reason:**
1. Click **Create**
2. Enter reason name (e.g., "Lack of experience")
3. Optionally, select an email template to send when using this reason
4. Save

**💡 Tip:** Keep reasons professional and non-discriminatory. These are for your internal tracking.

---

#### Step 3: Set Up Application Tags

**Why this matters:** Tags help you quickly categorize and find candidates.

1. Go to **Configuration** → **Tags**
2. Review default tags: Reserve, Manager, IT, Sales
3. Create tags relevant to your company

**Suggested tags to create:**
- **By Source:** Referral, LinkedIn, Campus Hire, Job Fair
- **By Status:** Hot Lead, Silver Medal, Future Leader
- **By Preferences:** Remote OK, Relocatable, Immediate Joiner
- **By Type:** Internship, Fresher, Experienced, Executive

**To create a tag:**
1. Click **Create**
2. Enter tag name
3. Pick a color (helps visual recognition)
4. Save

**💡 Tip:** Use tags consistently across your team. Create a shared list of what each tag means.

---

### Day 2: Create Your First Job Position

**⏱️ Time needed:** 20 minutes per job

#### Tutorial: Creating a Job Posting

**Scenario:** You need to hire a Marketing Manager.

**Step-by-step:**

1. **Navigate to Jobs**
   - Click **Recruitment** → **Jobs**
   - Click **Create** button (top-left)

2. **Fill Basic Information**
   ```
   Job Position: Marketing Manager
   Department: Marketing (select from dropdown)
   Recruiter: [Your Name] (select yourself)
   No. of Recruitment: 1 (how many people you're hiring)
   ```

3. **Add Job Description**
   - Click on **Description** tab
   - Write or paste your job description
   - Use the rich text editor to format:
     - **Bold** for section headings
     - Bullet points for responsibilities
     - Bullet points for requirements

   **Example Structure:**
   ```
   About the Role:
   We're looking for a creative Marketing Manager to lead our brand...

   Key Responsibilities:
   • Develop marketing strategies
   • Manage social media campaigns
   • Analyze campaign performance
   • Lead a team of 3 marketers

   Requirements:
   • 5+ years marketing experience
   • Experience with digital marketing
   • Strong analytical skills
   • Bachelor's degree in Marketing or related field

   What We Offer:
   • Competitive salary
   • Health insurance
   • Remote work options
   • Professional development budget
   ```

4. **Set Up Email for Applications**
   - Go to **Recruitment** tab
   - The system automatically creates an email alias like:
     `marketing-manager-5@company.com`
   - Anyone who emails this address will automatically become an applicant
   - **Note down this email** to use in your job postings

5. **Add Interviewers** (Optional)
   - In **Recruitment** tab, click **Add** under Interviewers
   - Select team members who will interview candidates
   - They'll automatically get access to view applicants

6. **Save**
   - Click **Save** (top-left)

**✅ Congratulations!** Your first job is created.

---

#### What Happens Next?

Once saved:
- ✓ Job appears in your Jobs list
- ✓ Email alias is active and ready to receive applications
- ✓ You can start adding applicants manually
- ✓ You can publish it to your website (we'll cover this later)

---

### Day 3: Understand How to Receive Applications

There are 3 main ways candidates enter your system:

#### Method 1: Email Applications (Automatic)

**How it works:**
1. Candidate sends resume to `marketing-manager-5@company.com`
2. System automatically creates an applicant record
3. Sets them to "New" stage
4. You get a notification
5. Their resume is attached automatically

**You don't do anything - it's automatic! 🎉**

---

#### Method 2: Manual Entry

**When to use:** Walk-in candidates, referrals, or someone sends to your personal email.

**Step-by-step:**

1. Go to **Recruitment** → **Applications**
2. Click **Create**
3. Fill in the form:

```
Subject: Application for Marketing Manager - Sarah Mitchell
Applicant's Name: Sarah Mitchell
Email: sarah.mitchell@email.com
Phone: +91-98765-43210
Applied Job: Marketing Manager (select from dropdown)
Recruiter: [Auto-filled, usually you]
Department: [Auto-filled from job]
Stage: New (or choose appropriate stage)
```

4. **Upload Documents:**
   - Scroll down to **Attachments** section
   - Drag and drop their resume
   - Add cover letter if they sent one

5. **Add Notes** (optional):
   - Scroll to bottom
   - Click in the "Log note" box
   - Type any initial impressions: "Referral from John in Sales. Strong background in B2B marketing."

6. **Click Save**

---

#### Method 3: Website Applications (Automatic)

**Prerequisites:** Website module must be set up (advanced feature).

**How it works:**
1. You publish the job to your company website
2. Candidates fill out an online application form
3. System automatically creates applicant record
4. You get notified

**We'll cover website setup in Advanced Features section.**

---

### Day 4: Learn to Manage Applications

#### Tutorial: Reviewing Your First Applicant

**Scenario:** Sarah Mitchell applied for Marketing Manager. Let's review her application.

**Step 1: Find the Application**

1. Click **Recruitment** → **Applications**
2. You'll see the Kanban view (cards organized by stages)
3. Look in the **New** column
4. Find Sarah's card

**What you see on the card:**
- Name: Sarah Mitchell
- Job: Marketing Manager
- Priority stars (you can click to set priority)
- Email icon (click to send email)
- Phone icon (click to call)

---

**Step 2: Open the Applicant**

1. Click on Sarah's card
2. Full application opens

**What you'll see:**

**Top Section:**
- Subject line
- Applicant name
- Job position
- Stage (with buttons to move to other stages)
- Priority stars

**Left Side - Details:**
- Email address (clickable to send email)
- Phone number (clickable to call if you have phone integration)
- LinkedIn profile
- Applied Job
- Department
- Recruiter (assigned to)
- Interviewers
- Expected Salary
- Proposed Salary
- Availability Date
- Tags

**Bottom - Tabs:**
- **Chatter:** All communication history (emails sent, notes, meetings)
- **Attachments:** Resume and other files

---

**Step 3: Review the Resume**

1. Scroll to **Attachments** section
2. Click on the resume file name
3. It opens in preview
4. Read through the resume

---

**Step 4: Make Initial Assessment**

**Good fit? Let's move forward:**

1. Click the **Stage** dropdown at the top
2. Select **Qualification**
3. The application moves to the next stage
4. If you configured an email template, it automatically sends an acknowledgment email to Sarah

**Not a good fit? Let's refuse professionally:**

1. Click the **Refuse** button (top of the page)
2. A popup appears asking for a reason
3. Select reason: "Does not fit job requirements"
4. Check the box "Send email" if you want to notify them
5. Select email template (e.g., "Refusal Email")
6. Click **Refuse**
7. Application is marked as refused and archived

---

**Step 5: Add Notes**

**Always document your thoughts!**

1. Scroll to the bottom (Chatter section)
2. Click **Log note**
3. Type your assessment:
   ```
   Resume Review:
   ✓ 6 years marketing experience in tech companies
   ✓ Led successful product launches
   ✓ Strong digital marketing background
   ✗ No team management experience
   
   Decision: Move to phone screen. Ask about leadership potential.
   ```
4. Click **Log**

**💡 Tip:** Notes are only visible to your team, not the candidate. Be honest and detailed - it helps everyone involved in hiring.

---

### Day 5: Learn to Communicate with Applicants

#### Tutorial: Sending Your First Email

**Scenario:** Sarah moved to Qualification stage. You want to schedule a phone interview.

**Step 1: Open Email Composer**

1. Open Sarah's application
2. Click **Send Email** button (top of page)
3. Email composer opens

---

**Step 2: Choose Email Type**

**Option A: Use a Template (Recommended)**

1. Click the **Load template** dropdown
2. Select "Interview Invitation"
3. Template loads with pre-written text
4. Placeholders are automatically filled:
   - `${object.partner_name}` becomes "Sarah Mitchell"
   - `${object.job_id.name}` becomes "Marketing Manager"

**Example template:**
```
Dear Sarah Mitchell,

Thank you for applying to the Marketing Manager position at [Company Name].

We were impressed with your background and would like to schedule a phone 
interview with you.

Are you available for a 30-minute call this week? Please suggest 2-3 time 
slots that work for you.

Looking forward to speaking with you!

Best regards,
[Your Name]
Recruiter
```

**Option B: Write Custom Email**

1. Leave template blank
2. Write your own message
3. You can use formatting:
   - **Bold**, *Italic*
   - Bullet points
   - Links

---

**Step 3: Customize and Send**

1. Edit the template to personalize:
   ```
   Hi Sarah,

   Thanks for applying to our Marketing Manager role!

   I reviewed your resume and I'm particularly impressed with your product 
   launch experience at TechCorp. I'd love to learn more about that.

   Are you available for a 30-minute phone call this week? Please suggest 
   2-3 times that work for you (preferably between 10 AM - 5 PM IST).

   Best,
   [Your Name]
   ```

2. **Attach files** (if needed):
   - Click **Attach a file**
   - Upload job description, company brochure, etc.

3. **Review:**
   - Check recipient email is correct
   - Read through your message

4. **Send:**
   - Click **Send** button
   - Email is sent immediately
   - A copy is logged in the Chatter section

**✅ Done!** Sarah receives your email, and you have a record of all communication.

---

#### Tutorial: Logging a Phone Call

**Scenario:** You just called Sarah and had a 15-minute phone screen.

**Step 1: Log the Call**

1. Open Sarah's application
2. Scroll to Chatter section
3. Click **Log note**

**Step 2: Document Details**

Type your notes:
```
Phone Screen - 15 minutes (Feb 12, 2026)

Discussion Points:
• Confirmed 6 years marketing experience, primarily B2B tech
• Discussed TechCorp product launch - increased sales by 40%
• Currently managing contractors, no direct reports
• Salary expectation: ₹12-15 LPA (within our budget)
• Notice period: 30 days
• Very interested in the role, loves our company mission

Red Flags:
• No experience managing full-time team members

Assessment:
Strong candidate. Communication skills excellent. 
Move to in-person interview with Marketing Director.

Next Steps:
• Schedule interview with Director
• Send pre-interview assignment (content strategy brief)
```

**Step 3: Update Application**

1. **Set Priority:**
   - Click the stars at the top
   - Set to 2 stars (Very Good)

2. **Update Expected Salary:**
   - Edit mode
   - Expected Salary: 1200000 (₹12 LPA)
   - Proposed Salary: 1400000 (₹14 LPA, your offer range)

3. **Add Tags:**
   - Click Tags field
   - Add "Hot Lead"
   - Add "Remote OK" (if she mentioned flexibility)

4. **Move Stage:**
   - Change stage to "First Interview"

5. **Save**

**💡 Tip:** The more detail you log, the better. If someone else needs to take over, they'll have full context.

---

---

## Daily Tasks & Tutorials

### Your Daily Routine

Here's a suggested workflow for managing recruitment daily:

#### Morning Routine (15 minutes)

**1. Check New Applications**

```
Recruitment → Applications → Kanban View
Look at "New" column
```

**What to do:**
- Review new applications from overnight/previous day
- Quick scan of resumes
- Move promising ones to "Qualification"
- Refuse obvious mismatches

**💡 Tip:** Set a goal to review all "New" applications within 24 hours. Candidates appreciate quick responses!

---

**2. Check Scheduled Activities**

```
Click on your name (top-right) → My Dashboard → Activities
Or
Recruitment → Applications → Filters → My Activities
```

**You'll see:**
- Phone calls you need to make today
- Interviews scheduled
- Follow-ups due
- Document requests

**Mark activities as done:**
- Click the checkmark when completed
- Add any notes
- System removes from your to-do list

---

#### Afternoon Routine (30 minutes)

**3. Move Pipeline Forward**

```
Recruitment → Applications → Kanban View
```

**Review each stage from left to right:**

**Qualification Stage:**
- Review resumes in detail
- Schedule phone screens
- Send rejection emails if not fit

**First Interview Stage:**
- Schedule in-person/video interviews
- Send calendar invites
- Prepare interview questions

**Second Interview Stage:**
- Coordinate with hiring managers
- Schedule team interviews
- Review feedback from first interview

**Offer Stage:**
- Prepare offer letters
- Get approvals if needed
- Send offers

---

**4. Update Communication**

- Respond to candidate emails (from Chatter)
- Send pending interview invitations
- Follow up on pending items

---

#### Weekly Tasks

**Every Monday Morning:**

**Review Full Pipeline**
```
Recruitment → Applications → Graph View
Group by: Stage
```

**Ask yourself:**
- Which stages have too many candidates stuck?
- Which positions are moving slowly?
- Do I need to source more candidates?

---

**Check Source Performance**
```
Recruitment → Applications → Graph View
Group by: Source
```

**Questions:**
- Which sources bring the most applicants?
- Which bring the best quality?
- Should I invest more in certain channels?

---

### Tutorial: Conducting the Full Hiring Process

Let's walk through hiring someone from start to finish.

#### Phase 1: Application Received

**What happened:** John Davis applied for "Senior Developer" via email.

**Your actions:**

1. **Notification arrives:** "New application for Senior Developer"

2. **Quick review in Kanban:**
   - See John's card in "New" stage
   - Click to open

3. **Initial assessment:**
   - Download and read resume
   - Check email/LinkedIn
   - Read cover letter

4. **Decision point:**
   - **Good fit?** → Move to Qualification
   - **Not fit?** → Refuse with reason
   - **Unsure?** → Add tag "Need Second Opinion" and assign to hiring manager

5. **Log notes:**
   ```
   Initial Resume Review:
   ✓ 8 years Python/Django experience
   ✓ Led teams of 5+
   ✓ Strong GitHub profile
   ? Salary expectations unknown
   
   Action: Moving to phone screen
   ```

---

#### Phase 2: Qualification

**Objective:** Detailed resume review and phone screen.

**Actions:**

1. **Detailed resume analysis:**
   - Check LinkedIn profile
   - Review GitHub (if developer)
   - Google their name (check online presence)
   - Check references (if mentioned)

2. **Send phone screen invitation:**
   ```
   Send Email → Use "Phone Screen Invitation" template

   Customize:
   Hi John,

   Thanks for applying! Your experience with Django caught my eye.

   Would you be available for a 30-minute phone call to discuss 
   the role? Please suggest 2-3 times this week.

   Best,
   [Name]
   ```

3. **Schedule call:**
   - Candidate replies with availability
   - Click **Schedule Meeting**
   - Fill details:
     - Subject: Phone Screen - John Davis - Senior Developer
     - Start Date: [Pick date/time]
     - Duration: 30 minutes
     - Attendees: [You + any other screener]
   - Click **Save**
   - Calendar invite sent automatically

4. **Prepare for call:**
   - Review resume again
   - Prepare 5-10 questions
   - Log notes with questions to ask

---

#### Phase 3: Phone Screen

**You just finished a 30-minute call with John.**

**Immediately after (while fresh):**

1. **Log the conversation:**
   ```
   Phone Screen - 30 min (Feb 12, 2026)

   Technical Background:
   ✓ Strong Python - 8 years professional
   ✓ Django expert - built 10+ production apps
   ✓ Experience with AWS, Docker, PostgreSQL
   ✓ Led team of 5 for 3 years
   
   Soft Skills:
   ✓ Excellent communication
   ✓ Asks thoughtful questions
   ✓ Passionate about code quality
   
   Logistics:
   ✓ Salary expectation: ₹20-25 LPA (our range: ₹22-28 LPA) ✓
   ✓ Notice period: 60 days
   ✓ Open to relocation to Bangalore
   ✓ Prefers hybrid work (3 days office, 2 days remote)
   
   Concerns:
   ? Limited experience with our specific tech stack (FastAPI)
   ? No experience in fintech (our industry)
   
   Gut Feeling: 8/10
   Strong technical skills, great culture fit, enthusiastic
   
   Recommendation: PROCEED TO TECHNICAL INTERVIEW
   ```

2. **Update application:**
   - Priority: 3 stars (Excellent)
   - Expected Salary: 2000000
   - Proposed Salary: 2400000
   - Tags: Add "Hot Lead", "Relocatable", "Team Leader"

3. **Move to next stage:**
   - Stage: First Interview
   - Add activity: "Schedule technical interview within 3 days"

4. **Coordinate next steps:**
   - Email hiring manager: "Great candidate, please review notes"
   - Send technical test (if your process includes it)
   - Schedule technical interview

---

#### Phase 4: Technical Interview

**Scenario:** Your technical lead interviewed John.

**Actions:**

1. **Collect feedback:**
   - Ask technical lead for written feedback
   - If they have access, they can log notes directly
   - If not, you log their feedback:

   ```
   Technical Interview - 60 min (Feb 14, 2026)
   Interviewer: Priya Sharma (Tech Lead)

   Technical Assessment:
   ✓ Solved coding challenge efficiently
   ✓ Explained thought process clearly
   ✓ Good understanding of system design
   ✓ Wrote clean, readable code
   ✓ Asked good questions about our architecture
   
   Code Review:
   ✓ Reviewed sample code from our codebase
   ✓ Identified potential issues
   ✓ Suggested improvements
   
   Areas to Develop:
   • Needs to learn FastAPI (minor, quick to learn)
   • Limited microservices experience
   
   Priya's Recommendation: STRONG HIRE
   Score: 9/10
   
   Quote: "Best candidate I've interviewed in 6 months. 
   Bring him in for team interview ASAP."
   ```

2. **Decision:**
   - Consensus: Move forward
   - Next step: Team interview + Manager interview

3. **Schedule final interview:**
   ```
   Schedule Meeting
   - Subject: Final Interview - John Davis
   - Duration: 2 hours
   - Attendees: Engineering Manager, 2 team members, HR
   - Location: Office / Video call
   ```

4. **Send invitation to John:**
   ```
   Hi John,

   Great news! Priya was very impressed with your technical skills.

   We'd like to invite you for a final round interview with our 
   engineering team and manager. This will be a 2-hour session 
   covering:
   - Team dynamics and collaboration (1 hour)
   - Manager interview (30 min)
   - Your questions (30 min)

   [Date/time options]

   Looking forward to seeing you!
   ```

---

#### Phase 5: Final Interview

**The team loved John!**

**Actions:**

1. **Collect all feedback:**
   ```
   Final Interview Panel - 2 hours (Feb 16, 2026)

   Engineering Manager (Rajesh Kumar):
   ✓ Strong leadership potential
   ✓ Aligns with company values
   ✓ Interested in mentoring juniors
   Score: 9/10 - HIRE

   Team Member 1 (Amit):
   ✓ Would love to work with him
   ✓ Collaborative mindset
   ✓ Good technical depth
   Score: 8/10 - HIRE

   Team Member 2 (Sneha):
   ✓ Great cultural fit
   ✓ Asked insightful questions about our product
   ✓ Excited about our mission
   Score: 9/10 - HIRE

   CONSENSUS: EXTEND OFFER
   ```

2. **Move to Offer stage:**
   - Change stage to "Contract Proposal"

3. **Prepare offer:**
   - Salary: ₹24 LPA (within budget, top of his expectation)
   - Benefits: Health insurance, remote options, learning budget
   - Start date: Allow 60-day notice period

4. **Get approvals:**
   - Create activity for manager: "Approve offer for John Davis"
   - Wait for approval

---

#### Phase 6: Offer Extended

**Approval received. Time to make the offer!**

**Actions:**

1. **Call John first (personal touch):**
   - Deliver good news verbally
   - Build excitement
   - Confirm salary and benefits verbally
   - Mention official email coming

2. **Send official offer email:**
   ```
   Send Email → Use "Offer Letter" template

   Subject: Job Offer - Senior Developer at [Company]

   Dear John,

   We are delighted to offer you the position of Senior Developer 
   at [Company]!

   The team was unanimously impressed with your skills, experience, 
   and enthusiasm. We believe you'll be a great addition to our 
   engineering team.

   Offer Details:
   • Position: Senior Developer
   • Department: Engineering
   • Salary: ₹24,00,000 per annum
   • Benefits: [List benefits]
   • Start Date: [60 days from acceptance]
   • Work Mode: Hybrid (3 days office, 2 days remote)

   Please find the detailed offer letter attached. Review and let us 
   know your decision by [deadline - typically 5-7 days].

   We're excited about the possibility of you joining our team!

   Best regards,
   [Your Name]

   Attachments: Offer_Letter_John_Davis.pdf
   ```

3. **Log the offer:**
   ```
   Offer Extended (Feb 17, 2026)
   
   Offer Details:
   • Position: Senior Developer
   • CTC: ₹24 LPA
   • Join Date: April 18, 2026 (60 days)
   • Offer valid until: Feb 24, 2026
   
   Status: Awaiting candidate response
   ```

4. **Update fields:**
   - Proposed Salary: 2400000
   - Availability: April 18, 2026

5. **Create follow-up activity:**
   - Activity: "Follow up on offer if no response in 3 days"
   - Due Date: Feb 20, 2026

---

#### Phase 7: Offer Accepted!

**John accepted! 🎉**

**Actions:**

1. **Log acceptance:**
   ```
   OFFER ACCEPTED! (Feb 18, 2026)
   
   John called and verbally accepted the offer.
   Expected to receive signed offer letter by Feb 19.
   Start date confirmed: April 18, 2026
   
   Next steps:
   • Receive signed documents
   • Create employee record
   • Begin onboarding process
   ```

2. **Move to final stage:**
   - Stage: Contract Signed

3. **Create employee record:**
   - Click **Create Employee** button (top of application)
   - System pre-fills information:
     - Name: John Davis
     - Email: john.davis@email.com
     - Phone: +91-98765-43210
     - Job: Senior Developer
     - Department: Engineering
   - Add additional info:
     - Employee ID: (auto-generated or manual)
     - Join Date: April 18, 2026
     - Address details
     - Emergency contact
   - Click **Create**

4. **System automatically:**
   - Links employee to applicant
   - Marks applicant as "Hired"
   - Archives the application
   - Copies all attachments to employee record

5. **Send welcome email:**
   ```
   Hi John,

   Congratulations and welcome to the [Company] family! 🎉

   We're thrilled to have you joining us on April 18, 2026.

   You'll receive a separate email from our HR team with:
   • Onboarding checklist
   • First-day instructions
   • Equipment setup
   • Required documents

   If you have any questions before your start date, feel free 
   to reach out anytime.

   See you soon!
   
   Best,
   [Your Name]
   ```

6. **Notify relevant people:**
   - Email engineering team: "John Davis joining April 18"
   - Email IT: "New joiner - setup laptop"
   - Email admin: "Prepare desk/access cards"

**✅ Hiring process complete!** John is now in the system as an employee.

---

#### Phase 8: What About the Other Candidates?

**You interviewed 5 people for this role. John got the job. What about the other 4?**

**Candidate: Sarah (Second choice, very good)**

1. **Add to Talent Pool:**
   - Open Sarah's application
   - Click **Action** → **Add to Talent Pool**
   - Select pool: "Engineering Talent Pool"
   - Add tag: "Silver Medal - Senior Developer"
   
2. **Send professional rejection:**
   ```
   Hi Sarah,

   Thank you for interviewing for our Senior Developer position.

   This was a very competitive process, and while we were impressed 
   with your background, we've decided to move forward with another 
   candidate whose experience more closely matches our immediate needs.

   However, we'd love to stay in touch for future opportunities. 
   May we keep your information on file?

   We wish you the best in your job search!

   Best regards,
   [Your Name]
   ```

3. **Refuse application:**
   - Click **Refuse**
   - Reason: "Job already fulfilled"
   - Don't send auto-email (you sent custom one above)

**Candidates: Amit, Lisa, Kevin (Good but not quite right)**

1. **Add best ones to Talent Pool** (Amit and Lisa)
   - Same process as Sarah

2. **Send polite rejections:**
   ```
   Thank you for your interest in [Company]. After careful 
   consideration, we've decided to move forward with other 
   candidates. We appreciate the time you invested in our 
   process and wish you the best!
   ```

3. **Refuse applications:**
   - Reason: "Does not fit job requirements" or "Job already fulfilled"

---

## Advanced Features

### Setting Up Skills Matching

**What this does:** Automatically score candidates based on how well their skills match the job requirements.

#### Step 1: Enable Skills

**Check if installed:**
1. Go to **Apps** (main menu)
2. Search: "Skills"
3. Look for "Skills Management"
4. If not installed, click **Install**

#### Step 2: Create Skill Types

**Skill Types are categories of skills.**

1. Click your name (top-right) → **Settings**
2. Search for "Skills" or go to **Employees** app → **Configuration** → **Skill Types**
3. Click **Create**

**Examples to create:**

```
Skill Type: Programming Languages
Skill Type: Frameworks & Tools
Skill Type: Soft Skills
Skill Type: Certifications
Skill Type: Spoken Languages
```

#### Step 3: Create Individual Skills

1. Go to **Employees** → **Configuration** → **Skills**
2. For each skill:

**Technical Skills Example:**
```
Skill: Python
Skill Type: Programming Languages
Levels:
  • Beginner (Proficiency: 25%)
  • Intermediate (Proficiency: 50%)
  • Advanced (Proficiency: 75%)
  • Expert (Proficiency: 100%)
```

```
Skill: Django
Skill Type: Frameworks & Tools
Levels: [Same as above]
```

```
Skill: Team Leadership
Skill Type: Soft Skills
Levels: [Same as above]
```

**Create 20-30 skills relevant to your hiring needs.**

**💡 Tip:** Start with skills you commonly look for. You can always add more later.

---

#### Step 4: Add Skills to Job Positions

1. Go to **Recruitment** → **Jobs**
2. Open a job (e.g., "Senior Developer")
3. Click **Edit**
4. Go to **Requirements** tab
5. Under **Skills**, click **Add a line**

**Example for Senior Developer:**
```
Skill: Python          | Level: Expert
Skill: Django          | Level: Advanced
Skill: PostgreSQL      | Level: Intermediate
Skill: Team Leadership | Level: Intermediate
Skill: AWS             | Level: Intermediate
```

6. **Save**

---

#### Step 5: Add Skills to Applicants

**When reviewing a resume:**

1. Open applicant
2. Click **Edit**
3. Go to **Skills** tab
4. Click **Add a line**

**Example for John's application:**
```
Skill: Python          | Level: Expert     | ✓ Matches required
Skill: Django          | Level: Expert     | ✓ Exceeds required
Skill: PostgreSQL      | Level: Advanced   | ✓ Exceeds required
Skill: Team Leadership | Level: Intermediate | ✓ Matches required
Skill: FastAPI         | Level: Beginner   | Not required (bonus)
```

5. **Save**

---

#### Step 6: View Match Score

**Automatically calculated!**

On the applicant record, you'll see:
```
Match Score: 95%

Matching Skills:
✓ Python (Expert)
✓ Django (Expert)
✓ PostgreSQL (Advanced)
✓ Team Leadership (Intermediate)

Missing Skills:
✗ AWS (Intermediate required)
```

---

#### Step 7: Filter by Match Score

1. Go to **Applications**
2. Click **Filters**
3. Add Custom Filter:
   - Field: Match Score
   - Operator: ≥ (greater than or equal)
   - Value: 70

**Result:** See only candidates with 70%+ match.

**💡 Pro Tip:** Sort by match score to prioritize high-scoring candidates.

---

### Setting Up Talent Pools

**When to use:** You want to maintain a database of good candidates for future roles.

#### Creating Your First Talent Pool

**Scenario:** You want to build a pool of marketing professionals.

1. **Navigate:**
   - Click **Recruitment** → **Talent Pools**

2. **Create:**
   - Click **Create**

3. **Fill details:**
   ```
   Name: Marketing Professionals 2026
   Pool Manager: [Your Name]
   Description: High-quality marketing candidates from 
                Q1 2026 hiring. Focus on digital marketing
                and content strategy backgrounds.
   Color: [Pick a color, e.g., Blue]
   ```

4. **Save**

---

#### Adding Candidates to Talent Pool

**Method 1: From Applicant Record**

1. Open an applicant (e.g., Sarah who didn't get hired)
2. Click **Action** → **Add to Talent Pool**
3. Select pool: "Marketing Professionals 2026"
4. Add tags: "Digital Marketing", "Content Strategy", "Silver Medal"
5. Click **Add to Pool**

**Method 2: Bulk Add**

1. Go to **Applications**
2. Select multiple applicants (checkbox)
3. Click **Action** → **Add to Talent Pool**
4. Same process

**Method 3: From Talent Pool**

1. Open talent pool
2. Click **Add Applicants** button
3. Search and filter applicants
4. Select candidates
5. Click **Add**

---

#### Using Talent Pools

**Scenario:** New marketing position opened. Search your pool first!

1. **Open Talent Pool:**
   - **Recruitment** → **Talent Pools**
   - Click "Marketing Professionals 2026"

2. **View talents:**
   - Click **Talents** smart button (shows count)
   - See all candidates in pool

3. **Filter talents:**
   - Use tags to filter
   - Example: Filter by "Content Strategy" tag

4. **Find duplicates:**
   - Click **Find Duplicates** (top button)
   - System checks for duplicate emails/phones
   - Helps clean up your pool

5. **Apply to new job:**
   - Select candidates (checkbox)
   - Click **Action** → **Apply to Job**
   - Select job: "Content Marketing Manager"
   - Select initial stage: "Qualification" (skip "New" since you know them)
   - Click **Create Applications**

**Result:** 
- Applications created for all selected candidates
- They start at Qualification stage
- They're linked to new job
- You can immediately reach out to them

**💡 Benefit:** Instead of posting and waiting, you have pre-screened candidates ready to interview!

---

#### Organizing Multiple Talent Pools

**Recommended pool structure:**

```
By Function:
• Engineering Talent Pool
• Marketing Talent Pool
• Sales Talent Pool
• Design Talent Pool

By Seniority:
• Junior Talent Pool
• Mid-Level Talent Pool
• Senior Leadership Pool

By Source:
• Campus Recruits 2026
• Employee Referrals
• LinkedIn Premium Candidates

By Status:
• Silver Medal Candidates (close 2nd choice)
• Future Leaders
• Passive Candidates
```

**💡 Tip:** Don't create too many pools. 5-10 well-organized pools are better than 50 scattered ones.

---

### Publishing Jobs to Website

**Prerequisites:** Website module must be installed.

#### Step 1: Prepare Job for Publishing

1. Open the job position
2. Click **Edit**
3. Fill **Description** tab completely:
   - Rich, detailed job description
   - Clear requirements
   - Benefits
   - Company culture info

4. Go to **Website** tab
5. Fill:
   ```
   Website Description: (for SEO, 150-160 characters)
   "Senior Software Engineer needed in Mumbai. Python/Django expert. 
   Join our innovative fintech team. 5+ years exp. Apply now!"
   
   Job Details: (additional info for website)
   • Work mode: Hybrid (3 days office)
   • Office location: Andheri, Mumbai
   • Team size: 15 engineers
   • Benefits: Health insurance, learning budget
   ```

---

#### Step 2: Publish to Website

1. Check the box: **Website Published**
2. **Save**

**That's it!** Job is now live on your website.

---

#### Step 3: View on Website

1. Click **Go to Website** button (top of job record)
2. Your website opens showing the job listing

**URL format:**
```
yourcompany.com/jobs
yourcompany.com/jobs/detail/senior-software-engineer-15
```

---

#### Step 4: See Published Jobs List

**Candidate view:**
1. Go to `yourcompany.com/jobs`
2. See all published jobs
3. Use filters:
   - Department
   - Location
   - Remote/On-site
4. Search by keywords

---

#### What Candidates See

**Job Listing Page:**
- Job title
- Department
- Location
- Publication date
- Brief description

**Job Detail Page:**
- Full description
- Requirements
- Benefits
- Apply button
- Application form

**Application Form:**
- Name (required)
- Email (required)
- Phone (required)
- LinkedIn profile
- Upload Resume (required)
- Cover letter/message
- Submit button

---

#### What Happens When Someone Applies

1. **Candidate fills form** on website
2. **Clicks Submit**
3. **System automatically:**
   - Creates applicant record
   - Assigns to the job
   - Sets stage to "New"
   - Attaches their resume
   - Tracks where they came from (website)
4. **You get notified:** "New application received"
5. **Candidate sees:** "Thank you! Your application has been received."
6. **Confirmation email** sent to candidate (if configured)

**You didn't do anything - it's all automatic! 🎉**

---

#### Tips for Website Publishing

**✓ DO:**
- Write compelling job descriptions
- Use keywords candidates search for
- Update when job details change
- Unpublish when position is filled
- Make descriptions mobile-friendly

**✗ DON'T:**
- Publish draft/incomplete jobs
- Use internal jargon
- Forget to unpublish after hiring
- Copy-paste generic descriptions

---

### Setting Up Email Automation

**Goal:** Automatically send emails when candidates move to certain stages.

#### Step 1: Create Email Templates

1. **Enable Developer Mode:**
   - Go to **Settings**
   - Scroll to bottom
   - Click **Activate Developer Mode**

2. **Navigate to Email Templates:**
   - **Settings** → **Technical** → **Email** → **Templates**

3. **Create Template:**
   - Click **Create**

**Example: Acknowledgment Email**

```
Name: Recruitment - Application Received

Model: Applicant (hr.applicant)

Email:
  To: ${object.email_from}
  Subject: Application Received - ${object.job_id.name}

Body:
Dear ${object.partner_name or 'Applicant'},

Thank you for applying for the ${object.job_id.name} position at ${object.company_id.name}.

We have received your application and our team will review it shortly. 
If your qualifications match our requirements, we will contact you within 
5-7 business days for the next steps.

We appreciate your interest in joining our team!

Best regards,
${object.user_id.name}
${object.company_id.name} Recruitment Team
```

**Save**

---

**Create More Templates:**

**Interview Invitation:**
```
Subject: Interview Invitation - ${object.job_id.name}

Dear ${object.partner_name},

We are pleased to invite you for an interview for the ${object.job_id.name} position.

Interview Details:
• Date & Time: [To be scheduled]
• Duration: [30-60 minutes]
• Format: [Phone/Video/In-person]

Please reply with your availability, and we'll send a calendar invitation.

Looking forward to speaking with you!

Best regards,
${object.user_id.name}
```

**Rejection Email:**
```
Subject: Application Update - ${object.job_id.name}

Dear ${object.partner_name},

Thank you for your interest in the ${object.job_id.name} position and for 
taking the time to interview with us.

After careful consideration, we have decided to move forward with other 
candidates whose qualifications more closely match our current needs.

We appreciate your time and effort and wish you the best in your job search.

Best regards,
${object.company_id.name} Recruitment Team
```

---

#### Step 2: Link Templates to Stages

1. **Go to Stages:**
   - **Recruitment** → **Configuration** → **Stages**

2. **Edit a stage:**
   - Click on "Qualification" stage

3. **Set Email Template:**
   - Field: **Email Template**
   - Select: "Recruitment - Application Received"
   - **Save**

**Now, whenever you move an applicant to "Qualification" stage, they automatically receive the acknowledgment email!**

---

**Set up automation for other stages:**

```
Stage: Qualification → Email: Application Received
Stage: First Interview → Email: Interview Invitation
Stage: Refused → Email: Rejection Email (use refusal reason emails)
Stage: Contract Signed → Email: Welcome Email
```

---

#### Step 3: Test the Automation

1. **Create a test applicant** (use your own email)
2. **Move to Qualification** stage
3. **Check your email** - you should receive the auto-email
4. **Check Chatter** - email should be logged

**✅ If it works, set up is complete!**

---

### Using Survey/Assessment Forms

**When to use:** You want candidates to complete tests, questionnaires, or assessments.

#### Prerequisites

1. **Install Survey module:**
   - **Apps** → Search "Survey"
   - Install "Survey"

2. **Install Recruitment Survey Integration:**
   - **Apps** → Search "Recruitment Survey"
   - Install "Survey: Recruitment Integration"

---

#### Step 1: Create an Interview Survey

1. **Go to Surveys:**
   - Main menu → **Surveys**

2. **Create New Survey:**
   - Click **Create**

**Example: Technical Assessment for Developers**

```
Survey Title: Python Developer Technical Assessment

Description:
This assessment tests your Python programming knowledge and 
problem-solving skills. Please complete within 48 hours.
Time estimate: 45 minutes

Questions:

[Section 1: Python Basics]

Q1: What is the output of the following code?
[Code snippet]
• Option A
• Option B
• Option C
• Option D

Q2: Explain the difference between list and tuple in Python.
[Text Answer]

Q3: Write a function to reverse a string.
[Code Answer - Multiple Lines]

[Section 2: Django Framework]

Q4: What is Django ORM?
[Text Answer]

Q5: Explain the MTV pattern.
[Text Answer]

[Section 3: Problem Solving]

Q6: Coding Challenge
Write a function that [specific problem].

Requirements:
• Input: [specify]
• Output: [specify]
• Constraints: [specify]

[Code Answer Field]
```

3. **Configure Survey Settings:**
   - **Options** tab:
     - ✓ Login Required (prevent spam)
     - Access Mode: "Anyone with the link"
     - Scoring: Set if you want automatic scoring
     - Time Limit: 60 minutes (optional)

4. **Save & Close**

---

#### Step 2: Link Survey to Job

1. **Open Job Position:**
   - **Recruitment** → **Jobs** → Select job

2. **Edit Job:**
   - Go to **Recruitment** tab
   - Field: **Interview Form**
   - Select: "Python Developer Technical Assessment"
   - **Save**

---

#### Step 3: Send Survey to Candidate

**Method 1: From Applicant Record**

1. Open applicant (e.g., John)
2. Click **Send Interview** button (top)
3. Popup appears:
   ```
   Survey: Python Developer Technical Assessment
   Email To: john@email.com
   Deadline: [Feb 15, 2026 - 7 days from now]
   ```
4. Email preview shows:
   ```
   Hi John,

   As part of our hiring process, we'd like you to complete 
   a technical assessment.

   Please click the link below to begin:
   [Unique survey link]

   Please complete by: Feb 15, 2026

   If you have any questions, feel free to reach out.

   Best regards,
   [Your Name]
   ```
5. **Send**

---

**Method 2: Bulk Send**

1. **Applications** list
2. Select multiple applicants
3. **Action** → **Send Interview**
4. Same process, sent to all

---

#### Step 4: Track Responses

**On Applicant Record:**

You'll see:
```
Interview Forms: 1 response

[Click to view]
```

**View Response:**
1. Click on the response
2. See all answers
3. See score (if auto-scored)
4. Download PDF of responses

---

#### Step 5: Evaluate

**In applicant's Chatter, log your evaluation:**

```
Technical Assessment Review:

Score: 85/100 (auto-scored)

Strengths:
✓ Strong Python fundamentals (100% on basics)
✓ Good understanding of Django ORM
✓ Clean, well-commented code

Areas for Improvement:
• Limited knowledge of advanced Django features
• Coding challenge was correct but not optimized

Overall: PASS
Move to technical interview to discuss solutions.
```

---

### Tracking Application Sources (UTM)

**What this does:** Tracks where candidates come from so you know which job posting sites work best.

#### Understanding UTM

**UTM = Urchin Tracking Module** (you don't need to remember this!)

**Simply put:** Special links that tell you where clicks came from.

**Example:**

Normal link:
```
yourcompany.com/jobs/detail/senior-developer-5
```

UTM link for LinkedIn:
```
yourcompany.com/jobs/detail/senior-developer-5
?utm_campaign=Q1_Tech_Hiring
&utm_medium=Social_Media
&utm_source=LinkedIn
```

When someone clicks this link and applies, you'll know they came from LinkedIn.

---

#### Step 1: Create UTM Campaign

1. **App Menu** → **Recruitment** → **Configuration** → **Campaigns** (if not visible, enable in Settings)

   OR

   **Settings** → **Technical** → **Marketing** → **UTM Campaigns**

2. **Create Campaign:**
   ```
   Campaign Name: Q1 Tech Hiring 2026
   ```

---

#### Step 2: Create UTM Medium

**Medium = The type of source**

1. **Configuration** → **Medium**
2. Create:
   ```
   Social Media
   Job Board
   Referral
   Email Campaign
   Campus Event
   ```

---

#### Step 3: Create UTM Source

**Source = Specific website/platform**

1. **Configuration** → **Source**
2. Create:
   ```
   LinkedIn
   Indeed
   Naukri
   Twitter
   Employee Referral
   IIT Bombay Career Fair
   ```

---

#### Step 4: Create Job Source with UTM

1. **Open Job Position**
2. Go to **Recruitment** tab
3. Under **Job Sources**, click **Add a line**
4. Fill:
   ```
   Source Name: LinkedIn Tech Jobs
   Campaign: Q1 Tech Hiring 2026
   Medium: Social Media
   Source: LinkedIn
   ```
5. **Save**

**System generates:**
```
URL: yourcompany.com/jobs/detail/senior-developer-5
     ?utm_campaign=Q1_Tech_Hiring_2026
     &utm_medium=Social_Media
     &utm_source=LinkedIn
```

6. **Copy this URL**

---

#### Step 5: Post with UTM Links

**When posting jobs:**

- **LinkedIn:** Use the UTM link for LinkedIn
- **Indeed:** Create separate source, use its UTM link
- **Naukri:** Create separate source, use its UTM link
- **Email to referrals:** Create "Referral" source, use its UTM link

**💡 Key:** Use different UTM links for different sources!

---

#### Step 6: Track Performance

**After a few weeks of receiving applications:**

1. **Go to Applications**
2. **Switch to Graph View**
3. **Group by: Source**

**You'll see:**
```
LinkedIn: 25 applications
Indeed: 50 applications
Naukri: 30 applications
Referral: 10 applications
```

**Now, check quality:**

Filter by hired:
```
LinkedIn: 3 hired
Indeed: 1 hired
Naukri: 2 hired
Referral: 3 hired
```

**Analysis:**
- Referrals: 10 applications, 3 hired = 30% conversion! 🎯
- LinkedIn: 25 applications, 3 hired = 12% conversion
- Indeed: 50 applications, 1 hired = 2% conversion

**Action:** Invest more in referrals and LinkedIn, reduce Indeed spend.

---

## Optimization Tips by Role

### Optimizing for Technical Roles (Developers, Engineers)

#### Job Setup

**Required Fields:**
```
✓ Job Title: Be specific (e.g., "Senior Backend Developer (Python)" not just "Developer")
✓ Department: Engineering
✓ Skills Required (Priority: MUST configure):
  - Programming Languages: Python (Expert), JavaScript (Intermediate)
  - Frameworks: Django (Advanced), React (Intermediate)
  - Tools: Git (Advanced), Docker (Intermediate)
  - Soft Skills: Problem Solving (Advanced), Team Collaboration (Intermediate)
✓ Expected Degree: Bachelor's in Computer Science (or equivalent experience)
✓ Interviewers: Add Technical Lead + Senior Developer
```

**Job Description Template:**
```
[About the Role]
Concise 2-3 sentence overview

[What You'll Do]
• Specific technical responsibilities
• Technologies you'll work with
• Projects you'll contribute to

[What We're Looking For]
• X years of experience with [specific tech]
• Proven experience building [specific systems]
• Strong understanding of [concepts]

[Nice to Have]
• Optional but valuable skills

[Tech Stack]
Our current stack: [List everything]

[What We Offer]
• Learning budget
• Tech conferences
• Latest equipment
• Flexible hours
• Remote options
```

---

#### Screening Process

**Stage 1: Resume Screen**
- Check GitHub profile (if provided)
- Look for relevant projects
- Check skills match score (use Skills feature)
- **Goal:** Filter to top 30%

**Stage 2: Phone Screen (15-20 min)**
- Confirm technical background
- Assess communication skills
- Discuss salary expectations
- **Goal:** Filter to top 15%

**Stage 3: Technical Assessment**
- Send coding test (use Survey feature)
- 2-3 hours take-home or 1-hour live coding
- **Goal:** Filter to top 5%

**Stage 4: Technical Interview (60 min)**
- Deep dive into technical skills
- System design discussion
- Code review
- **Goal:** Filter to top 2-3 candidates

**Stage 5: Cultural/Team Fit (60 min)**
- Meet the team
- Manager interview
- Candidate asks questions
- **Decision point:** Hire or not

---

#### Using Skills Matching Effectively

**Create detailed skill requirements:**

```
Must Have (Weight: High):
• Python: Expert level
• Django/FastAPI: Advanced level
• PostgreSQL: Intermediate level
• Git: Advanced level

Good to Have (Weight: Medium):
• React: Intermediate level
• Docker: Intermediate level
• AWS: Beginner level

Soft Skills (Weight: High):
• Problem Solving: Advanced
• Communication: Intermediate
```

**Filter applicants:**
- Minimum match score: 70%
- Prioritize 85%+ for immediate interviews

---

#### Talent Pool Strategy

**Create specialized pools:**
```
• Frontend Developers Pool
• Backend Developers Pool
• Full Stack Developers Pool
• DevOps Engineers Pool
• Junior Developers Pool (for mentorship programs)
```

**Tag system:**
```
By Expertise:
• Python Expert
• JavaScript Expert
• Cloud Native

By Availability:
• Immediate Joiner
• 30-Day Notice
• Passive Candidate

By Source:
• GitHub Recruit
• Tech Conference
• Hackathon Winner
```

---

### Optimizing for Sales Roles

#### Job Setup

**Required Fields:**
```
✓ Job Title: Specific (e.g., "Enterprise B2B Sales Manager" not "Sales Person")
✓ Department: Sales
✓ Skills:
  - Sales Methodology: SPIN Selling (Advanced)
  - CRM Tools: Salesforce (Intermediate)
  - Industry Knowledge: B2B SaaS (Advanced)
  - Soft Skills: Negotiation (Advanced), Relationship Building (Expert)
✓ Expected Results: ₹X revenue target, Y deals per quarter
```

**Job Description Focus:**
```
[Opportunity]
• Revenue potential
• Uncapped commission
• Career growth path

[What Success Looks Like]
• Revenue targets
• Deal sizes
• Sales cycle length

[Ideal Candidate]
• X years selling [product type]
• Track record of [specific achievement]
• Experience with [customer segment]

[Compensation]
• Base: ₹X
• Variable: ₹Y (realistic OTE)
• Accelerators
```

---

#### Screening Process

**Stage 1: Resume Screen**
- Check: Previous companies, products sold, quotas achieved
- Look for: Consistent quota attainment, industry experience
- **Filter criteria:** Top 40%

**Stage 2: Phone Screen (20 min)**
- Sales assessment: Listen to how they sell themselves
- Check: Energy, enthusiasm, communication
- Discuss: Quotas achieved, deal sizes, sales cycle
- **Filter to:** Top 20%

**Stage 3: Sales Exercise**
- Role-play: Sell our product to you
- Or: Create a 30-60-90 day plan
- **Filter to:** Top 10%

**Stage 4: Final Interview**
- Meet sales leader
- Dive into specific deals they closed
- Check references
- **Decision**

**❗Key:** Sales hiring is about ENERGY and TRACK RECORD. If they can't sell themselves in the interview, they can't sell your product.

---

#### Talent Pool Strategy

```
Pools:
• Enterprise Sales Pool
• SMB Sales Pool
• Inside Sales Pool
• Sales Leadership Pool

Tags:
• Top Performer (quota >120%)
• Industry - SaaS
• Industry - Fintech
• Enterprise Experience
• Startup Experience
• Hunter (new biz)
• Farmer (account mgmt)
```

---

### Optimizing for Marketing Roles

#### Job Setup

**Skills to Track:**
```
Technical Skills:
• SEO/SEM: [Level]
• Content Marketing: [Level]
• Analytics (Google Analytics): [Level]
• Marketing Automation (HubSpot/Marketo): [Level]
• Social Media Marketing: [Level]

Creative Skills:
• Copywriting: [Level]
• Design Tools (Canva/Figma): [Level]

Analytical Skills:
• Data Analysis: [Level]
• Campaign ROI Tracking: [Level]
```

**Job Description Focus:**
```
[Impact]
What campaigns/results they'll own

[Creativity + Data]
Balance of creative work and analytical work

[Tools]
Specific tools they'll use

[Portfolio]
Request portfolio/work samples
```

---

#### Screening Process

**Stage 1: Resume + Portfolio Screen**
- **MUST:** Request portfolio, work samples, or campaign case studies
- Review: Quality of work, diversity of campaigns, results achieved
- **Filter:** Top 30%

**Stage 2: Phone Screen**
- Discuss specific campaigns from portfolio
- Assess: Strategic thinking, creativity, metrics focus
- **Filter:** Top 15%

**Stage 3: Assignment**
- "Create a go-to-market strategy for [product]"
- Or: "Review our current website and suggest improvements"
- **Filter:** Top 5%

**Stage 4: Presentation + Interview**
- Present assignment
- Meet team
- **Decision**

---

#### Talent Pool Strategy

```
Pools:
• Digital Marketers Pool
• Content Creators Pool
• Growth Marketers Pool
• Brand Managers Pool

Tags:
• B2B Marketing
• B2C Marketing
• Performance Marketing
• Content Strategy
• SEO Specialist
• Paid Ads Expert
```

---

### Optimizing for Leadership/Management Roles

#### Job Setup

**Different Approach:**

```
Focus Areas:
• Leadership experience: Years managing teams
• Team size managed
• Budget managed
• Strategic accomplishments

Skills:
• People Management: Expert
• Strategic Planning: Advanced
• Budget Management: Advanced
• Change Management: Advanced
• Industry Expertise: [Specific domain]
```

**Job Description:**
```
[The Challenge]
What problem this leader will solve

[Leadership Scope]
• Team size
• Budget
• Key responsibilities
• Strategic initiatives

[Ideal Background]
• X years in leadership
• Experience with [specific challenges]
• Industry background

[What We Offer Leaders]
• Impact potential
• Resources
• Growth opportunities
• Compensation package
```

---

#### Screening Process

**More stages, deeper assessment:**

**Stage 1: Executive Resume Screen**
- Check: Career progression, company brands, scope of responsibility
- **Filter:** Top 20%

**Stage 2: Recruiter Phone Screen (30 min)**
- Leadership philosophy
- Strategic accomplishments
- Cultural fit
- Compensation alignment
- **Filter:** Top 10%

**Stage 3: Case Study/Assignment**
- Strategic challenge related to the role
- Written deliverable
- **Filter:** Top 5%

**Stage 4: Interview Panel (2-3 hours)**
- Meet: Board members, senior leadership, key stakeholders
- Discuss: Case study, experience, vision
- **Filter:** Top 2-3

**Stage 5: Reference Checks**
- Speak with former reports, peers, bosses
- Deep dive into leadership style

**Stage 6: Final Discussion**
- Compensation negotiation
- Offer

**⏱️ Timeline:** Leadership hiring takes 6-12 weeks typically.

---

#### Talent Pool Strategy

```
Pools:
• VP-Level Talent Pool
• Director-Level Talent Pool
• Emerging Leaders Pool
• Functional Experts Pool (CFOs, CTOs, etc.)

Tags:
• Startup Experience
• Enterprise Experience
• Scale-up Specialist
• Turnaround Expert
• Hypergrowth Experience
• [Specific industry tags]
```

---

### Optimizing for Entry-Level/Fresh Graduate Roles

#### Job Setup

**Focus on Potential:**

```
Skills:
• Focus on soft skills over hard skills
• Learning ability
• Teamwork
• Communication

Requirements:
• Recent graduate or final year
• Specific degree (if needed)
• GPA threshold (if relevant)
• Internship experience (bonus)
```

**Job Description:**
```
[Learning Opportunity]
What they'll learn

[Mentorship]
Who will guide them

[Growth Path]
Career progression

[Ideal Candidate]
• Eagerness to learn
• Strong fundamentals
• Cultural fit
• Passion for [industry/domain]
```

---

#### Screening Process

**Faster, higher volume:**

**Stage 1: Resume Screen**
- Check: Degree, GPA, internships, projects, extra-curriculars
- **Filter:** Top 40% (higher volume than experienced roles)

**Stage 2: Online Assessment (optional)**
- Aptitude test
- Technical basics test
- **Filter:** Top 20%

**Stage 3: Phone/Video Screen (15 min)**
- Energy, enthusiasm, communication
- Learning mindset
- **Filter:** Top 10%

**Stage 4: Interview**
- Team fit
- Problem-solving approach
- Willingness to learn
- **Decision**

**⏱️ Timeline:** Campus hiring can process 100+ candidates in 2-3 weeks.

---

#### Talent Pool Strategy

```
Pools:
• Campus Recruits 2026
• Campus Recruits 2027
• Intern-to-FTE Pipeline
• [Specific college pools]

Tags:
• IIT/NIT/[Top colleges]
• Gold Medalist
• Hackathon Winner
• Internship Completed
• Sports/Leadership
```

**💡 Pro Tip:** Build relationships with campus placement cells. Add promising students to talent pool even if not hiring immediately.

---

## Common Scenarios

### Scenario 1: High-Volume Hiring (10+ positions)

**Challenge:** You need to hire 15 customer support agents quickly.

**Strategy:**

1. **Setup:**
   - Create job: "Customer Support Agent"
   - No. of Recruitment: 15
   - Simplified stages: New → Screen → Interview → Offer → Hired

2. **Sourcing:**
   - Post on multiple job boards
   - Use different UTM links to track
   - Employee referral campaign

3. **Screening:**
   - Use assessment test to pre-screen (Survey module)
   - Only strong scorers (85%+) get phone screen
   - Batch interviews: Schedule 5-10 per day

4. **Batch Processing:**
   - Send bulk emails
   - Batch refuse unqualified
   - Group interviews (panel interviewing multiple candidates)

5. **Quick Decisions:**
   - Same-day decisions after interview
   - Rolling offers (don't wait to interview all)
   - Accept first 15 who meet the bar

**💡 Key:** Speed is critical in volume hiring. Simplify process, use automation heavily

.

---

### Scenario 2: Passive Candidate Outreach

**Challenge:** You need a very specific skill set. Candidates don't apply; you need to find them.

**Strategy:**

1. **Manual Sourcing:**
   - LinkedIn search
   - GitHub search (for developers)
   - Conference attendee lists
   - Competitor companies

2. **Create Applicant Manually:**
   - **Recruitment** → **Applications** → **Create**
   - Name: [Found on LinkedIn]
   - Email: [From LinkedIn]
   - Job: Senior Data Scientist
   - Stage: "Outreach" (create this stage)
   - Tag: "Passive Candidate", "LinkedIn Source"

3. **Personalized Outreach:**
   ```
   Hi [Name],

   I came across your profile on LinkedIn and was impressed with your 
   work on [specific project].

   We're building [exciting thing] at [Company] and I think your 
   background in [skill] would be a perfect fit.

   Would you be open to a quick 15-minute conversation to learn more? 
   No commitment required - just exploring if there's a mutual fit.

   Best,
   [Your Name]
   ```

4. **Track in System:**
   - Log all outreach emails in Chatter
   - Track responses
   - Move through stages as they warm up

5. **Build Relationship:**
   - Even if not interested now, add to Talent Pool
   - Tag: "Passive", "Future Opportunity"
   - Follow up every 3-6 months

---

### Scenario 3: Internal Promotion/Transfer

**Challenge:** An existing employee wants to apply for a different role.

**Strategy:**

1. **Create Application:**
   - **Applications** → **Create**
   - Unlike external candidate, skip resume since you have employee record

2. **Link to Employee:**
   - Fill field: **Link to Employee**
   - Select the employee from list

3. **Modified Process:**
   - May skip early stages
   - Different interview focus (fit for new role vs. company culture)
   - Coordinate with current manager

4. **Decision:**
   - If hired: System updates employee record
   - If not: Professional feedback, keep for future roles

**💡 Benefit:** Using recruitment system for internal transfers maintains consistency and transparency.

---

### Scenario 4: Replacing a Previous Hire

**Challenge:** Someone you hired 3 months ago didn't work out. Need to replace quickly.

**Strategy:**

1. **Review Previous Candidates:**
   - Open the job position
   - View all applicants
   - Filter by: Refused + Tag "Silver Medal"
   - These were your 2nd, 3rd choice candidates

2. **Re-engage:**
   - **Unarchive** their applications
   - **Reset to Qualification** stage
   - Send email:
     ```
     Hi [Name],

     I hope you're doing well. We spoke a few months ago about our 
     [Job Title] position.

     The position is open again, and I immediately thought of you. 
     Your background is still a great fit.

     Would you be interested in revisiting the conversation?

     Best,
     [Your Name]
     ```

3. **Fast-Track:**
   - They already interviewed once
   - May skip some stages
   - Quick decision

**⏱️ Benefit:** Hire in 1-2 weeks instead of 6-8 weeks.

---

### Scenario 5: Seasonal/Contract Hiring

**Challenge:** You need 5 interns for summer (3-month contract).

**Strategy:**

1. **Create Separate Job:**
   - Job Title: "Summer Intern - Marketing"
   - Clearly mark as "Internship" in description
   - Duration: 3 months
   - Start date: June 1

2. **Campus Outreach:**
   - Partner with universities
   - Campus recruitment drives
   - Create UTM source: "IIT Bombay Career Fair"

3. **Simplified Process:**
   - Stages: New → Screen → Interview → Offer → Hired
   - Assessment can be projects/assignments
   - Group interviews

4. **Create Talent Pool:**
   - Add all interviewed interns to "Intern Alumni Pool"
   - Tag with college name, year
   - When they graduate, recruit for full-time

**💡 Strategy:** Internship programs are talent pool builders for future full-time hiring.

---

### Scenario 6: Diversity Hiring Initiative

**Challenge:** You want to improve diversity in your engineering team.

**Strategy:**

1. **Track Diversity:**
   - Create tags: "Women in Tech", "Diversity Candidate"
   - Not visible to candidate, just internal tracking

2. **Targeted Sourcing:**
   - Post on diversity-focused job boards
   - Create UTM source for each
   - Partner with women in tech groups
   - College outreach to underrepresented groups

3. **Build Diverse Talent Pool:**
   - "Women in Tech Talent Pool"
   - "Diversity Engineering Pool"
   - Engage even when not actively hiring

4. **Bias-Free Process:**
   - Use skills matching (objective)
   - Standardized interviews
   - Diverse interview panels

5. **Track Metrics:**
   - % of diverse candidates at each stage
   - Identify drop-off points
   - Improve process

**📊 Report:**
```
Applications → Pivot Table
Rows: Stage
Columns: Tag "Women in Tech"
Values: Count
```

**💡 Ethical Note:** Use diversity tracking for positive action (targeted sourcing, bias reduction), never for discrimination.

---

## Quick Reference

### Daily Keyboard Shortcuts

**When in Applications list:**
- `C` - Create new application
- `J/K` - Move up/down in list
- `Enter` - Open selected application
- `Esc` - Close application

**In Kanban view:**
- Drag cards to move stages
- Click star to set priority
- Click email icon to send email

---

### Email Template Variables

Use these in your email templates:

```
${object.partner_name} - Candidate name
${object.job_id.name} - Job title
${object.email_from} - Candidate email
${object.partner_phone} - Candidate phone
${object.user_id.name} - Recruiter name
${object.department_id.name} - Department
${object.salary_proposed} - Your offered salary
${object.company_id.name} - Company name
${object.company_id.phone} - Company phone
${object.company_id.email} - Company email
```

---

### Filters You'll Use Often

**In Applications:**

1. **My Applications**
   - Filters → Recruiter: [Your name]

2. **New This Week**
   - Filters → Create Date → This Week

3. **Urgent Follow-ups**
   - Filters → Priority: 3 stars
   - Stage: Not "New"

4. **Rotting Applications**
   - Filters → Last Update > 14 days ago

5. **Silver Medal Candidates**
   - Filters → Tags: "Silver Medal"

---

### When to Use Each View

**Kanban View:** Daily pipeline management, moving candidates
**List View:** Searching, filtering, data entry
**Calendar View:** Seeing scheduled interviews
**Graph View:** Weekly metrics review
**Pivot View:** Deep analysis, reports for management

---

### Mobile Tips

If using Odoo mobile app:

- ✓ Review applications on the go
- ✓ Send quick emails
- ✓ Update stages
- ✓ Log notes after calls
- ✓ Check notifications
- ✗ Avoid complex data entry
- ✗ Better to create jobs on desktop

---

## Troubleshooting

### Problem: Email alias not receiving applications

**Check:**
1. Is email server configured? (Ask IT/Admin)
2. Is alias active? (Open Job → Recruitment tab → Check alias email)
3. Test: Send email to the alias from your personal email
4. Check spam folder

**Solution:**
- Ask admin to verify email gateway settings
- May need to configure MX records

---

### Problem: Can't see some applications

**Possible reasons:**
1. **They're archived.** Click "Filters" → "Archived" to see them.
2. **You're filtering.** Clear all filters (click X on each filter tag).
3. **Different recruiter.** Someone else owns them.
4. **You don't have access rights.** Ask admin to check your user role.

---

### Problem: Skills match score not showing

**Check:**
1. Is "Skills Management" module installed?
2. Is "Recruitment Skills" module installed?
3. Did you add skills to the Job?
4. Did you add skills to the Applicant?

**If all yes:**
- Refresh the page
- The match score appears in Skills tab

---

### Problem: Stage email not sending automatically

**Check:**
1. Open Stage → Is email template selected?
2. Is email server configured?
3. Check Chatter → Was email logged as failed?

**Test:**
- Create test applicant with your email
- Move them to that stage
- Check if you received email

---

### Problem: Can't create employee from applicant

**Check:**
1. Is applicant in "Hired" stage (or a stage marked as "Hired Stage")?
2. Do you have permission to create employees?

**Workaround:**
- Ask HR admin to create employee
- Or ask admin to grant you employee creation rights

---

### Problem: Too many duplicate applications

**Solution:**
1. Go to Talent Pool → **Find Duplicates**
2. System shows duplicate emails/phones
3. **Link duplicates** to keep one, archive others
4. Or **Refuse duplicates** in batch

**Prevention:**
- Add note in job description: "Please apply only once"
- Check for duplicates weekly

---

### Problem: Talent pool getting messy

**Solution:**
1. Review quarterly
2. Remove candidates who:
   - Found jobs elsewhere
   - Not responding
   - No longer relevant
3. Update tags and information
4. Merge similar pools if too many

---

### Problem: Candidate says they didn't receive email

**Check:**
1. Open applicant → Chatter
2. Find the email in history
3. Check: Did it fail to send? (red error)
4. Check: Is their email correct?

**Solution:**
- Resend email
- Or copy email content and send manually
- Update email address if wrong

---

### Problem: Lost track of which candidates interviewed

**Solution:**
1. Use **Activities**: Create activity "Interview Completed" when done
2. Use **Tags**: Tag "Interviewed"
3. Use **Notes**: Always log interview notes immediately
4. Check **Calendar**: Meetings are linked to applicants

---

### Need More Help?

**In the system:**
- Click ❓ icon (top-right) → Documentation
- Or contact your system administrator

**Best practice:**
- Keep this guide bookmarked
- Print the "Quick Reference" section
- Share tips with your team

---

## Conclusion

### You're Ready to Start! 🎉

You now have everything you need to:
- ✅ Create and manage job positions
- ✅ Review and process applications
- ✅ Communicate professionally with candidates
- ✅ Build talent pools for future hiring
- ✅ Use skills matching to find best fits
- ✅ Track where your best candidates come from
- ✅ Optimize your process for different roles

---

### Remember the Key Principles

1. **Speed Matters:** Respond to applications within 24 hours
2. **Document Everything:** Future you (and your team) will thank you
3. **Be Professional:** Every interaction represents your company
4. **Use Talent Pools:** Don't lose good candidates
5. **Track Sources:** Know what works
6. **Personalize:** Templates are starting points, not final messages
7. **Keep Learning:** System gets better as you use it more

---

### Your First Two Weeks Action Plan

**Week 1:**
- ✓ Day 1: Configure stages and settings
- ✓ Day 2: Create your first job position
- ✓ Day 3: Learn to review applications
- ✓ Day 4: Practice sending emails
- ✓ Day 5: Review full pipeline

**Week 2:**
- ✓ Set up email automation
- ✓ Create talent pools
- ✓ Configure skills (if applicable)
- ✓ Track sources with UTM
- ✓ Establish daily routine

---

### Keep This Guide Handy

📌 Bookmark this page
📌 Share with new HR team members
📌 Refer back when learning new features
📌 Update with your own tips and learnings

---

### Questions or Feedback?

This guide is for you! If something is unclear or you'd like more examples of specific scenarios, reach out to your system administrator or team lead.

**Happy Hiring!** 🎯

---

**Document Version:** 1.0  
**Created:** February 12, 2026  
**For:** HR Team  
**System:** Odoo 19.0 Recruitment Module  

---

*"The best hiring systems are the ones your team actually uses. Keep it simple, stay consistent, and focus on finding great people." - Your Friendly Training Guide* 😊

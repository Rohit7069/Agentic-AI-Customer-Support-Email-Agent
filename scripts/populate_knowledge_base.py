"""Script to populate the FAISS knowledge base with sample documents."""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.vector_kb_service import VectorKBService


SAMPLE_DOCUMENTS = [
    # Technical Support
    {
        "title": "Troubleshooting Sync Issues",
        "content": (
            "If files aren't syncing: 1) Check your internet connection and ensure "
            "it's stable. 2) Restart the application completely. 3) Check folder "
            "permissions — ensure the app has read/write access. 4) Clear the sync "
            "cache from Settings > Advanced > Clear Cache. 5) If the issue persists, "
            "try reinstalling the application. Contact support if none of these steps "
            "resolve the problem."
        ),
        "category": "technical_support",
        "source_url": "https://docs.cloudsync.com/troubleshoot-sync",
    },
    {
        "title": "App Crashes on Startup",
        "content": (
            "If the application crashes on startup: 1) Ensure your operating system "
            "meets the minimum requirements (Windows 10+, macOS 12+, Ubuntu 20.04+). "
            "2) Update your graphics drivers. 3) Try running the app in compatibility "
            "mode. 4) Check if antivirus software is blocking the application. "
            "5) Delete the config file at ~/.cloudsync/config.json and restart."
        ),
        "category": "technical_support",
        "source_url": "https://docs.cloudsync.com/troubleshoot-crashes",
    },
    {
        "title": "File Upload Errors",
        "content": (
            "Common upload errors and solutions: Error 413 — File exceeds the maximum "
            "size limit of 10GB per file. Error 429 — Too many requests, please wait "
            "and retry. Error 500 — Server-side issue, please try again later. "
            "Ensure file names don't contain special characters. Check your remaining "
            "storage quota in Settings > Account > Storage."
        ),
        "category": "technical_support",
        "source_url": "https://docs.cloudsync.com/upload-errors",
    },
    {
        "title": "Two-Factor Authentication Setup",
        "content": (
            "To enable 2FA: go to Settings > Security > Two-Factor Authentication. "
            "You can use an authenticator app (Google Authenticator, Authy) or SMS. "
            "We recommend using an authenticator app for maximum security. "
            "Save your backup codes in a safe place — they can be used if you lose "
            "access to your 2FA device."
        ),
        "category": "technical_support",
        "source_url": "https://docs.cloudsync.com/2fa-setup",
    },
    # Billing
    {
        "title": "Billing FAQ - Common Questions",
        "content": (
            "Billing is monthly, charged on the same day each month. You can "
            "upgrade or downgrade your plan anytime from Settings > Billing. "
            "Pro-rated charges apply when changing plans mid-cycle. Refunds are "
            "available within 14 days of purchase. We accept Visa, MasterCard, "
            "American Express, and PayPal."
        ),
        "category": "billing",
        "source_url": "https://docs.cloudsync.com/billing-faq",
    },
    {
        "title": "Subscription Plans and Pricing",
        "content": (
            "Available plans: Free — 5GB storage, basic features. "
            "Personal ($9.99/mo) — 100GB storage, priority sync, version history. "
            "Professional ($19.99/mo) — 1TB storage, team collaboration, advanced "
            "sharing, API access. Enterprise (custom pricing) — unlimited storage, "
            "SSO, dedicated support, custom integrations. Annual billing saves 20%."
        ),
        "category": "billing",
        "source_url": "https://docs.cloudsync.com/pricing",
    },
    {
        "title": "Invoice and Payment History",
        "content": (
            "View your invoices at Settings > Billing > Payment History. "
            "Invoices are automatically emailed to your registered email address. "
            "You can update your billing email separately from your account email. "
            "Download invoices in PDF format for your records. Tax receipts are "
            "available for applicable regions."
        ),
        "category": "billing",
        "source_url": "https://docs.cloudsync.com/invoices",
    },
    {
        "title": "Refund Policy",
        "content": (
            "We offer full refunds within 14 days of purchase or renewal. "
            "To request a refund, contact support with your account email and "
            "order number. Refunds are processed within 5-7 business days. "
            "Partial refunds are available for annual subscriptions cancelled "
            "after 14 days, calculated on a pro-rata basis."
        ),
        "category": "billing",
        "source_url": "https://docs.cloudsync.com/refunds",
    },
    # Product Inquiry
    {
        "title": "Product Features Overview",
        "content": (
            "CloudSync offers: automatic file synchronization across all devices, "
            "real-time collaboration with team members, version history (up to 30 "
            "days on Pro), selective sync to save disk space, smart conflict "
            "resolution, end-to-end encryption for sensitive files, offline access "
            "mode, and integration with popular productivity tools."
        ),
        "category": "product_inquiry",
        "source_url": "https://docs.cloudsync.com/features",
    },
    {
        "title": "Supported Platforms and Integrations",
        "content": (
            "CloudSync is available on: Windows 10+, macOS 12+, Linux (Ubuntu, "
            "Fedora, Debian), iOS 15+, Android 12+, and Web browser. "
            "Integrations include: Slack, Microsoft Teams, Google Workspace, "
            "Notion, Trello, Jira, and Zapier for custom automations. "
            "API documentation is available at docs.cloudsync.com/api."
        ),
        "category": "product_inquiry",
        "source_url": "https://docs.cloudsync.com/platforms",
    },
    {
        "title": "Security and Privacy",
        "content": (
            "CloudSync uses AES-256 encryption for data at rest and TLS 1.3 "
            "for data in transit. We are SOC 2 Type II certified and GDPR "
            "compliant. Zero-knowledge encryption is available for Enterprise "
            "plans. We do not sell user data and maintain strict access controls. "
            "Regular security audits are conducted by independent third parties."
        ),
        "category": "product_inquiry",
        "source_url": "https://docs.cloudsync.com/security",
    },
    {
        "title": "Team Collaboration Features",
        "content": (
            "Team features include: shared folders with granular permissions "
            "(view, edit, admin), real-time co-editing of documents, commenting "
            "and @mentions, activity logs for all team actions, team storage "
            "management dashboard, and centralized billing for team admins. "
            "Teams can have up to 500 members on Enterprise plans."
        ),
        "category": "product_inquiry",
        "source_url": "https://docs.cloudsync.com/teams",
    },
    # Complaint
    {
        "title": "Handling Service Outages",
        "content": (
            "During service outages: we post real-time updates on status.cloudsync.com. "
            "Follow @CloudSyncStatus on Twitter for updates. Your files are safe — "
            "outages only affect sync operations, not stored data. Once service is "
            "restored, all pending syncs will complete automatically. We offer SLA "
            "credits for outages exceeding 4 hours for Enterprise customers."
        ),
        "category": "complaint",
        "source_url": "https://docs.cloudsync.com/outages",
    },
    {
        "title": "Data Loss Prevention and Recovery",
        "content": (
            "CloudSync maintains redundant backups across multiple data centers. "
            "If you believe files are missing: 1) Check the Trash folder (retained "
            "for 30 days). 2) Check version history for recent changes. 3) Verify "
            "selective sync settings. 4) Contact support immediately for data "
            "recovery assistance. We guarantee 99.99% data durability."
        ),
        "category": "complaint",
        "source_url": "https://docs.cloudsync.com/data-recovery",
    },
    {
        "title": "Escalation Process",
        "content": (
            "If your issue is not resolved satisfactorily: 1) Ask to speak "
            "with a Senior Support Engineer. 2) Request a ticket escalation "
            "with your case number. 3) Email executive@cloudsync.com for "
            "executive-level review. We aim to resolve all escalated issues "
            "within 24 hours. Enterprise customers have a dedicated account "
            "manager for direct escalation."
        ),
        "category": "complaint",
        "source_url": "https://docs.cloudsync.com/escalation",
    },
    # Feedback
    {
        "title": "Feature Request Process",
        "content": (
            "We love hearing your ideas! Submit feature requests at "
            "feedback.cloudsync.com. Our product team reviews all submissions "
            "monthly. Popular requests are prioritized — you can vote on existing "
            "requests. We'll notify you when a requested feature enters development. "
            "Beta access is available for users who submit feature requests."
        ),
        "category": "feedback",
        "source_url": "https://docs.cloudsync.com/feature-requests",
    },
    {
        "title": "Beta Program",
        "content": (
            "Join our beta program to test new features before release. "
            "Benefits include: early access to new features, direct channel "
            "to the product team, exclusive beta community forum, and special "
            "rewards for active beta testers. Sign up at beta.cloudsync.com. "
            "Beta versions may contain bugs — we recommend using a separate "
            "account for beta testing."
        ),
        "category": "feedback",
        "source_url": "https://docs.cloudsync.com/beta",
    },
    {
        "title": "Community and Support Resources",
        "content": (
            "Get help from our community: Community Forum at community.cloudsync.com, "
            "Knowledge Base at help.cloudsync.com, Video Tutorials on YouTube, "
            "Live Webinars every Wednesday at 2 PM EST. For direct support: "
            "use the in-app chat (24/7), email support@cloudsync.com (response "
            "within 4 hours), or call 1-800-CLOUDSYNC (M-F 9 AM - 6 PM EST)."
        ),
        "category": "feedback",
        "source_url": "https://docs.cloudsync.com/community",
    },
    # Other
    {
        "title": "Account Management",
        "content": (
            "Manage your account at Settings > Account. You can update your "
            "profile information, change your password, manage connected devices, "
            "set notification preferences, and configure privacy settings. "
            "To delete your account, go to Settings > Account > Delete Account. "
            "Account deletion is permanent and cannot be undone after 30 days."
        ),
        "category": "other",
        "source_url": "https://docs.cloudsync.com/account",
    },
    {
        "title": "Getting Started Guide",
        "content": (
            "Welcome to CloudSync! Quick start: 1) Download the app from "
            "cloudsync.com/download. 2) Sign in with your account. 3) Choose "
            "folders to sync. 4) Your files will automatically sync across all "
            "connected devices. Pro tip: use selective sync to save disk space "
            "on devices with limited storage."
        ),
        "category": "other",
        "source_url": "https://docs.cloudsync.com/getting-started",
    },
]


async def populate_knowledge_base():
    """Populate the FAISS knowledge base with sample documents."""
    print("🔄 Initializing Vector Knowledge Base...")
    kb_service = VectorKBService()
    await kb_service.initialize()

    print(f"📄 Adding {len(SAMPLE_DOCUMENTS)} documents to the knowledge base...")

    for i, doc in enumerate(SAMPLE_DOCUMENTS, 1):
        doc_id = await kb_service.add_document(
            title=doc["title"],
            content=doc["content"],
            category=doc["category"],
            source_url=doc["source_url"],
        )
        print(f"  ✅ [{i}/{len(SAMPLE_DOCUMENTS)}] Added: {doc['title']}")

    # Save the index to disk
    await kb_service.save()

    print(f"\n🎉 Knowledge base populated with {len(SAMPLE_DOCUMENTS)} documents!")
    print(f"   FAISS index saved to: {kb_service.index_path}")
    print(f"   Documents saved to: {kb_service.documents_path}")


if __name__ == "__main__":
    asyncio.run(populate_knowledge_base())

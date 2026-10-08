# Vault layout

The default layout. Users can rename, drop, or add folders. Every folder keeps an `executive.md`, and links get updated when things move.

## Support folders

| Folder | Holds | Doesn't hold |
| --- | --- | --- |
| `00 Inbox/` | Quick captures with no obvious home yet | Anything that already has a clear home |
| `Journal/` | One note per day (`YYYY/MM/YYYY-MM-DD.md`), plus weekly, monthly, and yearly reviews | Curated memories (those go in Happiness/Memories), plans |
| `DOCTRINES/` | Rules the owner has explicitly adopted, in their words | Book ideas not yet adopted (those go in Wisdom) |
| `Life Operations/` | Goals & Planning, Habits & Routines, Home & Life Admin, Digital Administration | Subject knowledge (link to the pillar instead) |
| `99 Archive/` | Retired, finished, or superseded material | Anything current |
| `_Templates/` | Daily Note, Person, Doctrine, Folder Guide | Real notes |

## The five pillars

| Pillar | Subfolders | Typical notes |
| --- | --- | --- |
| **Happiness** | Creative Inspiration, Hobbies & Interests, Memories, Self & Reflection | A hobby log, a favorite memory, personality notes |
| **Health** | Diet, Exercise, Sleep, Mental & Emotional Wellbeing, Medical & Care | A training plan, doctor list, sleep experiments |
| **Love** | Rolodex (Family, Friends, Romance, Mentors, Colleagues, Acquaintances, VIPs), Pets | One note per person, vet records |
| **Wealth** | My Accounting, My Businesses, My Career & Resume, My Side Hustles | Budget snapshots, resume, a business's "why" |
| **Wisdom** | Books & Courses, Frameworks & Mental Models, Faith & Philosophy, Psychology, Science, Economics, Languages, Math | One note per book, a mental model |

Each pillar also has a `<Pillar> — Principles.md`: what the owner believes about that area, in their own words.

## Edge cases

- **A note fits two pillars.** File it where the owner would look first and link from the other. Never keep two copies.
- **A person you also work with** gets one Rolodex note under the category that fits best. Business records about clients or employers stay in those businesses' own systems.
- **A plan versus reflection on the plan.** The plan lives in Life Operations/Goals & Planning; how it went goes in Journal, linked to the plan.
- **A memory versus a journal entry.** Journal is the running record. Memories holds the few worth curating, each linking back to its journal day.
- **A source versus an adopted rule.** The book note lives in Wisdom/Books & Courses. A rule the owner adopts from it becomes a DOCTRINES note that links to the book.
- **A topic outgrows a note.** Make a subfolder with its own `executive.md` (see executive-guides.md).
- **Attachments** (PDFs, images) sit next to the note that uses them. Make a `Reference Attachments/` subfolder inside the pillar if they pile up.

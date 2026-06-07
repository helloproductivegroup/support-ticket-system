export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { name, email, subject, message } = req.body;

  if (!name || !email || !subject || !message) {
    return res.status(400).json({ error: 'Missing required fields' });
  }

  // --- CATEGORY MAP ---
  // Category name → Airtable record ID (linked field requires record ID, not plain text)
  const CATEGORY_MAP = {
    'Network Issues':        'recJXoFousXPt8WY9',
    'Software Installation': 'recIRlkOumnwAIsHi',
    'Hardware Malfunction':  'recs29JP172Y0hlLs',
    'Password Reset':        'recoSAZxzkpKDkn12',
    'Email Problems':        'rechA0dmCMlPmBfix',
    'Access Request':        'recy0SmfHKJVCPGBi',
    'Onboarding':            'recQCZGvTWDKYYoaW',
    'Offboarding':           'recd0yBVCZ59nw4sg',
    'Printer Issues':        'recRzRfXPX37Pv7CL',
    'Facility Maintenance':  'rec5AFp7ruqhGOvKE',
    'Security Incident':     'rec6e0uyCUxz9JQCW',
    'Mobile Device Support': 'recGVtpR5ttYSp9QQ',
    'Meeting Room Booking':  'recbglEcwPIlL4YI4',
    'Expense Reimbursement': 'reckTdLphg1SFYi3t',
    'Payroll Inquiry':       'recC93wqOMkaS8g9x',
  };

  // --- AGENT ROSTER ---
  // Pre-fetched from Airtable. Each agent has their record ID, specializations,
  // and current workload score. Lower score = more available.
  const AGENTS = [
    { id: 'recMZ1T8Bs94SuDrH', name: 'Jessica Lee',    team: 'Technical Support',  specializations: ['Networking', 'Security'],             workload: 92 },
    { id: 'recUtVp17hAMZ6k4V', name: 'Michael Chen',   team: 'Customer Service',   specializations: ['Billing', 'Account Management'],      workload: 88 },
    { id: 'rec8oVn7xOkQvz9oP', name: 'Priya Patel',    team: 'Technical Support',  specializations: ['Software', 'Hardware'],               workload: 85 },
    { id: 'recYZoLm5kGsZgVeR', name: 'David Kim',      team: 'Customer Service',   specializations: ['Returns', 'Billing'],                 workload: 90 },
    { id: 'recXe88pL8EegSocS', name: 'Sara Martinez',  team: 'Technical Support',  specializations: ['Security', 'Cloud Services'],         workload: 95 },
    { id: 'rec4Z1opTvUyy8DFz', name: 'Ethan Brown',    team: 'Customer Service',   specializations: ['Account Management', 'General Inquiries'], workload: 87 },
    { id: 'recwIPYCvk1ZBfwhH', name: 'Linda Nguyen',   team: 'Technical Support',  specializations: ['Networking', 'Software'],             workload: 80 },
    { id: 'recb5Gc1uHxNohdkA', name: 'Carlos Rivera',  team: 'Customer Service',   specializations: ['Returns', 'General Inquiries'],       workload: 93 },
    { id: 'recj1W2Td2kvzzTRr', name: 'Emily Johnson',  team: 'Technical Support',  specializations: ['Hardware', 'Security'],               workload: 84 },
    { id: 'recvaaJQG6fyvNLWv', name: 'James Wilson',   team: 'Customer Service',   specializations: ['Billing', 'Account Management'],      workload: 82 },
    { id: 'rec43fZn5vXaKC5Bc', name: 'Ava Thompson',   team: 'Technical Support',  specializations: ['Cloud Services', 'Networking'],       workload: 91 },
    { id: 'recHxhoDkcsqGrldm', name: 'Noah Clark',     team: 'Customer Service',   specializations: ['General Inquiries', 'Returns'],       workload: 78 },
    { id: 'rect0JlzWi0THjUAZ', name: 'Sophia Garcia',  team: 'Technical Support',  specializations: ['Software', 'Hardware'],               workload: 89 },
    { id: 'recZ5gqU7pTV6Idhs', name: 'Benjamin Lee',   team: 'Customer Service',   specializations: ['Billing', 'Account Management'],      workload: 83 },
    { id: 'rec1v2b7silEqA1rx', name: 'Olivia Smith',   team: 'Technical Support',  specializations: ['Security', 'Networking'],             workload: 86 },
  ];

  // --- CATEGORY → SPECIALIZATION MAP ---
  // Maps each category to the agent specialization tag that best covers it.
  // This is what drives smart assignment.
  const CATEGORY_TO_SPEC = {
    'Network Issues':        'Networking',
    'Software Installation': 'Software',
    'Hardware Malfunction':  'Hardware',
    'Password Reset':        'General Inquiries',
    'Email Problems':        'Software',
    'Access Request':        'Security',
    'Onboarding':            'Account Management',
    'Offboarding':           'Account Management',
    'Printer Issues':        'Hardware',
    'Facility Maintenance':  'General Inquiries',
    'Security Incident':     'Security',
    'Mobile Device Support': 'Hardware',
    'Meeting Room Booking':  'General Inquiries',
    'Expense Reimbursement': 'Billing',
    'Payroll Inquiry':       'Billing',
  };

  // --- AGENT ASSIGNMENT LOGIC ---
  // 1. Find agents whose specializations include the relevant spec for this category
  // 2. Among those, pick the one with the lowest workload score
  // 3. If no match found, fall back to the lowest workload agent overall
  function assignAgent(category) {
    const targetSpec = CATEGORY_TO_SPEC[category];
    const matched = targetSpec
      ? AGENTS.filter(a => a.specializations.includes(targetSpec))
      : [];
    const pool = matched.length > 0 ? matched : AGENTS;
    return pool.reduce((best, agent) => agent.workload < best.workload ? agent : best);
  }

  try {
    // --- STEP A: Ask Claude to classify the ticket ---
    const claudeResponse = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': process.env.ANTHROPIC_API_KEY,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 1000,
        messages: [{
          role: 'user',
          content: `You are a support ticket classifier for an IT help desk. Analyze this support request and respond ONLY with valid JSON, no extra text, no markdown.

Customer name: ${name}
Subject: ${subject}
Message: ${message}

Available categories (pick the single best match): ${Object.keys(CATEGORY_MAP).join(', ')}

Respond with exactly this JSON structure:
{
  "category": "one of the exact category names listed above",
  "priority": "one of: Low, Medium, High",
  "ai_response": "a professional, empathetic 2-3 sentence reply to this customer acknowledging their issue and letting them know it has been logged and assigned"
}`
        }]
      })
    });

    if (!claudeResponse.ok) {
      throw new Error(`Claude API error: ${claudeResponse.status}`);
    }

    const claudeData = await claudeResponse.json();
    const aiText = claudeData.content[0].text;
    const aiResult = JSON.parse(aiText);

    // --- STEP B: Assign an agent based on category + workload ---
    const assignedAgent = assignAgent(aiResult.category);
    const categoryRecordId = CATEGORY_MAP[aiResult.category];

    // --- STEP C: Write the enriched ticket to Airtable ---
    const airtableResponse = await fetch(
      `https://api.airtable.com/v0/${process.env.AIRTABLE_BASE_ID}/Tickets`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${process.env.AIRTABLE_API_KEY}`
        },
        body: JSON.stringify({
          records: [{
            fields: {
              'Title':            subject,
              'Description':      message,
              'Customer Name':    name,
              'Customer Email':   email,
              'Status':           'New',
              'Priority':         aiResult.priority,
              'Category':         categoryRecordId ? [categoryRecordId] : [],
              'Assigned Agent':   [assignedAgent.id],
              'Communication Log': `AI Draft Response:\n\n${aiResult.ai_response}`,
              'Submission Date':  new Date().toISOString()
            }
          }]
        })
      }
    );

    if (!airtableResponse.ok) {
      const errorBody = await airtableResponse.text();
      throw new Error(`Airtable error: ${airtableResponse.status} - ${errorBody}`);
    }

    const airtableData = await airtableResponse.json();

    // --- STEP D: Return success to the form ---
    return res.status(200).json({
      success: true,
      ticketId: airtableData.records[0].id,
      category: aiResult.category,
      priority: aiResult.priority,
      assignedAgent: assignedAgent.name,
      message: aiResult.ai_response
    });

  } catch (error) {
    console.error('Ticket creation failed:', error.message);
    return res.status(500).json({
      success: false,
      error: 'Failed to process your request. Please try again.'
    });
  }
}

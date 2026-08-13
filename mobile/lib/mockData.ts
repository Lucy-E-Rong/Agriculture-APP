export const locations = [
  {
    id: "gh-1",
    name: "Greenhouse 1",
    shortId: "GH1",
    sections: [
      {
        id: "sec-a",
        name: "Section A",
        tables: [
          {
            id: "table-1",
            number: 1,
            rows: [
              { id: "row-1", number: 1, crop: "Romaine", stress: "low" },
              { id: "row-2", number: 2, crop: "Butterhead", stress: "medium" },
              { id: "row-3", number: 3, crop: null, stress: "none" }
            ]
          }
        ]
      }
    ]
  },
  {
    id: "gh-2",
    name: "Greenhouse 2",
    shortId: "GH2",
    sections: [
      {
        id: "sec-b",
        name: "Section B",
        tables: [
          {
            id: "table-2",
            number: 2,
            rows: [
              { id: "row-4", number: 1, crop: "Leaf lettuce", stress: "high" },
              { id: "row-5", number: 2, crop: "Romaine", stress: "low" }
            ]
          }
        ]
      }
    ]
  }
];

export const crops = [
  {
    id: "crop-1",
    name: "Lettuce",
    variety: "Romaine",
    location: "GH1 · SA · T1 · R1",
    plantedAt: "2026-05-03",
    stress: "low",
    lastScan: "18 min ago"
  },
  {
    id: "crop-2",
    name: "Lettuce",
    variety: "Butterhead",
    location: "GH1 · SA · T1 · R2",
    plantedAt: "2026-05-05",
    stress: "medium",
    lastScan: "2 hr ago"
  },
  {
    id: "crop-3",
    name: "Lettuce",
    variety: "Leaf lettuce",
    location: "GH2 · SB · T2 · R1",
    plantedAt: "2026-05-01",
    stress: "high",
    lastScan: "1 day ago"
  }
];

export const recentScans = [
  {
    id: "scan-1",
    crop: "Romaine",
    location: "GH1 · SA · T1 · R1",
    stress: "low",
    time: "18 min ago"
  },
  {
    id: "scan-2",
    crop: "Butterhead",
    location: "GH1 · SA · T1 · R2",
    stress: "medium",
    time: "2 hr ago"
  },
  {
    id: "scan-3",
    crop: "Leaf lettuce",
    location: "GH2 · SB · T2 · R1",
    stress: "high",
    time: "1 day ago"
  }
];


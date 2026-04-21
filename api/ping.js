// Vercel Serverless Function: Guardian Ping for Render API
// Rôle : Réveiller l'API sur Render toutes les 10 minutes via un Cron Job.

export default async function handler(req, res) {
  const RENDER_HEALTH_URL = "https://urban-data-explorer-api.onrender.com/api/health";
  
  console.log(`📡 Guardian: Pinging Render API at ${new Date().toISOString()}...`);
  
  try {
    const response = await fetch(RENDER_HEALTH_URL);
    const data = await response.json();
    
    return res.status(200).json({
      success: true,
      message: "Render API is awake!",
      timestamp: new Date().toISOString(),
      render_status: data
    });
  } catch (error) {
    console.error("❌ Guardian: Ping failed ->", error.message);
    return res.status(500).json({
      success: false,
      error: error.message
    });
  }
}

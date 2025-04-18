const request = require("supertest");
const app = require("../app");

describe("API Endpoints", () => {
  describe("GET /api/health", () => {
    it("should return status 200 and healthy: true", async () => {
      const res = await request(app).get("/api/health");
      expect(res.statusCode).toEqual(200);
      expect(res.body).toHaveProperty("healthy", true);
    });
  });

  // Add more test cases for your endpoints
});

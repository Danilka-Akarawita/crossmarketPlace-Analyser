import ChatWindow from "@/components/ChatWindow";

const pageStyles = {
  wrapper: {
    maxWidth: "1080px",
    margin: "0 auto",
    padding: "48px 24px 64px",
  },
  hero: {
    background: "linear-gradient(135deg, rgba(59,130,246,0.12), rgba(14,165,233,0.12))",
    borderRadius: "32px",
    padding: "40px 48px",
    display: "flex",
    flexDirection: "column" as const,
    gap: "22px",
    boxShadow: "0 30px 60px -40px rgba(15, 23, 42, 0.5)",
    border: "1px solid rgba(37, 99, 235, 0.18)",
    marginBottom: "42px",
  },
  heroTitle: {
    margin: 0,
    fontSize: "3rem",
    fontWeight: 700,
    letterSpacing: "-0.02em",
  },
  heroSubtitle: {
    margin: 0,
    fontSize: "1.08rem",
    lineHeight: 1.7,
    color: "#334155",
    maxWidth: "46rem",
  },
};

export default function HomePage() {
  return (
    <main>
      <div style={pageStyles.wrapper}>
        <section style={pageStyles.hero}>
          <h1 style={pageStyles.heroTitle}>Laptop Intelligence Concierge</h1>
          <p style={pageStyles.heroSubtitle}>
          Chat with a marketplace analyst that delivers concise product recommendations powered by AI
          </p>
        </section>

        <ChatWindow />
      </div>
    </main>
  );
}

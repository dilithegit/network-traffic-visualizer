function LogTable() {
  const logs = [
    ["14:02:11", "192.168.1.4", "10.0.0.1", "TCP", "64", "[SYN]"],
    ["14:02:11", "10.0.0.1", "192.168.1.4", "TCP", "64", "[SYN,ACK]"],
    ["14:02:12", "192.168.1.4", "8.8.8.8", "DNS", "82", "standard query"],
  ];

  return (
    <div className="border border-gray-600 mt-3">
      <h2 className="p-2 border-b border-gray-600 text-sm uppercase">
        Live Log Feed
      </h2>

      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-gray-500">
            {["TIME", "SOURCE IP", "DEST IP", "PROTOCOL", "LENGTH", "INFO"].map((h) => (
              <th key={h} className="text-left p-2">{h}</th>
            ))}
          </tr>
        </thead>

        <tbody>
          {logs.map((log, i) => (
            <tr key={i} className="border-b border-gray-300">
              {log.map((item, j) => (
                <td key={j} className="p-2">{item}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      <div className="text-center p-2 text-xs">
        • • • scrolling • • •
      </div>
    </div>
  );
}

export default LogTable;
// Register the Chart.js pieces we use once, at module load.
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
  Filler
);

ChartJS.defaults.animation = false;
ChartJS.defaults.font.family =
  "system-ui, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif";

export default ChartJS;

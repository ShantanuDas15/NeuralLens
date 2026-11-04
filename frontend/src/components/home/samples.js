import espressoImg from '../../assets/samples/espresso-cup.jpg';
import catImg from '../../assets/samples/window-cat.jpg';
import astronautImg from '../../assets/samples/astronaut.jpg';

// Real low-resolution JPEGs (public-domain scikit-image sample photos). They are
// uploaded through the normal enhance endpoint, so a click runs the real model.
export const SAMPLES = [
  { id: 'espresso', name: 'Espresso cup', filename: 'espresso-cup.jpg', src: espressoImg, width: 300, height: 200, alt: 'Low-resolution photo of an espresso cup on a wooden table' },
  { id: 'cat', name: 'Window cat', filename: 'window-cat.jpg', src: catImg, width: 300, height: 200, alt: 'Low-resolution photo of a cat' },
  { id: 'astronaut', name: 'Astronaut', filename: 'astronaut.jpg', src: astronautImg, width: 200, height: 200, alt: 'Low-resolution portrait of an astronaut' },
];

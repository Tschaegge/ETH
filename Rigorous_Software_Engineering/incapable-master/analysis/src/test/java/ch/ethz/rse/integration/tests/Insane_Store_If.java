
package ch.ethz.rse.integration.tests;

import ch.ethz.rse.Store;

// expected results:
// NON_NEGATIVE SAFE
// FITS_IN_TROLLEY UNSAFE
// FITS_IN_RESERVE SAFE

public class Insane_Store_If {
  public static void m1(int j){
    Store s;
    if(j<0) {
      s = new Store(2, 4);
    } else {
      s = new Store(1, 3);
    }

    s.get_delivery(2);

    
   }
 }


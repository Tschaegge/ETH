
package ch.ethz.rse.integration.tests;

import ch.ethz.rse.Store;

// expected results:
// NON_NEGATIVE SAFE
// FITS_IN_TROLLEY UNSAFE
// FITS_IN_RESERVE UNSAFE

public class Insane_Multiple_Args2 {
  public static void m1(int j, int k, int l){
    Store s = new Store(5, 10);
    for(int i = j; i < l; i++) {
      if(k>=0) {
        s.get_delivery(k);
      }
     
    }
    
    
   }
 }

